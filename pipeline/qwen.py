import json
import re
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from config import DO_SAMPLE, LORA_PATH, MAX_NEW_TOKENS, QWEN_MODEL_NAME, TEMPERATURE
from pipeline.prompt import build_messages

_tokenizer = None
_model = None

def _load_model():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model

    _tokenizer = AutoTokenizer.from_pretrained(QWEN_MODEL_NAME, trust_remote_code=True)

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    base = AutoModelForCausalLM.from_pretrained(
        QWEN_MODEL_NAME,
        quantization_config=quant,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    _model = PeftModel.from_pretrained(base, LORA_PATH, is_trainable=False)
    _model.eval()
    return _tokenizer, _model

def _extract_json(text):
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Qwen output did not contain a JSON object.")
    return json.loads(text[start:end + 1])

def generate_structured(document_text):
    tokenizer, model = _load_model()
    messages = build_messages(document_text)

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer([text], return_tensors="pt", padding=True).to(model.device)

    kwargs = {"max_new_tokens": MAX_NEW_TOKENS, "do_sample": DO_SAMPLE}
    if DO_SAMPLE:
        kwargs["temperature"] = TEMPERATURE

    with torch.inference_mode():
        outputs = model.generate(**inputs, **kwargs)

    generated = outputs[0][inputs["input_ids"].shape[-1]:]
    decoded = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return _extract_json(decoded)
