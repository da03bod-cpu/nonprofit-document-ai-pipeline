from functools import lru_cache

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

from config import LORA_REPO_ID, LORA_SUBFOLDER, MAX_NEW_TOKENS, QWEN_MODEL_NAME
from pipeline.prompt import build_messages

@lru_cache(maxsize=1)
def get_model():
    tokenizer = AutoTokenizer.from_pretrained(
        QWEN_MODEL_NAME,
        trust_remote_code=True,
        use_fast=False,
    )

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        QWEN_MODEL_NAME,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
    )

    model = PeftModel.from_pretrained(
        model,
        LORA_REPO_ID,
        subfolder=LORA_SUBFOLDER,
    )
    model.eval()

    return tokenizer, model

def generate(content: str) -> str:
    tokenizer, model = get_model()
    messages = build_messages(content)

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
        )

    generated = output[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)
