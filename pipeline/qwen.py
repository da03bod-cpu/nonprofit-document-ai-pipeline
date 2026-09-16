import json
import re
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from config import DO_SAMPLE, LORA_PATH, MAX_NEW_TOKENS, QWEN_CHUNK_CHARS, QWEN_MODEL_NAME, TEMPERATURE
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
        dtype=torch.bfloat16,
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


def _split_document(text, chunk_chars=QWEN_CHUNK_CHARS):
    text = text.strip()
    if len(text) <= chunk_chars:
        return [text]

    blocks = re.split(r"(?=^===== TABLE START =====$)", text, flags=re.M)
    chunks, current = [], ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        candidate = f"{current}\n{block}".strip() if current else block
        if current and len(candidate) > chunk_chars:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)

    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_chars:
            final_chunks.append(chunk)
            continue
        buf = ""
        for line in chunk.splitlines():
            candidate = f"{buf}\n{line}".strip() if buf else line
            if buf and len(candidate) > chunk_chars:
                final_chunks.append(buf)
                buf = line
            else:
                buf = candidate
        if buf:
            final_chunks.append(buf)
    return final_chunks


def _generate_one(document_text, chunk_index, total_chunks):
    tokenizer, model = _load_model()
    messages = build_messages(document_text, chunk_index, total_chunks)
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer([text], return_tensors="pt", padding=True).to(model.device)
    input_tokens = int(inputs["input_ids"].shape[-1])

    print("========== QWEN REQUEST ==========")
    print(f"CHUNK: {chunk_index}/{total_chunks}")
    print(f"DOCUMENT CHARS: {len(document_text)}")
    print(f"INPUT TOKENS: {input_tokens}")
    print(f"MAX NEW TOKENS: {MAX_NEW_TOKENS}")
    print("===================================")

    kwargs = {"max_new_tokens": MAX_NEW_TOKENS, "do_sample": DO_SAMPLE}
    if DO_SAMPLE:
        kwargs["temperature"] = TEMPERATURE

    with torch.inference_mode():
        outputs = model.generate(**inputs, **kwargs)

    generated = outputs[0][inputs["input_ids"].shape[-1]:]
    decoded = tokenizer.decode(generated, skip_special_tokens=True).strip()

    print("========== QWEN RAW OUTPUT ==========")
    print(decoded)
    print("========== END QWEN RAW OUTPUT ======")
    print(f"OUTPUT TOKENS: {int(generated.shape[-1])}")
    return _extract_json(decoded)


def _program_key(item):
    if not isinstance(item, dict):
        return None
    name = str(item.get("name") or "").strip()
    if not name:
        return None
    return (name, str(item.get("year")), str(item.get("beneficiaries_count")), str(item.get("budget")))


def _merge_results(results):
    merged, seen = [], set()
    for result in results:
        items = result.get("programs", []) if isinstance(result, dict) else (result if isinstance(result, list) else [])
        for item in items:
            if not isinstance(item, dict):
                continue
            key = _program_key(item)
            if key is not None and key in seen:
                continue
            if key is not None:
                seen.add(key)
            merged.append(item)
    return {"programs": merged}


def generate_structured(document_text):
    chunks = _split_document(document_text)
    print("========== QWEN DOCUMENT ==========")
    print(f"TOTAL DOCUMENT CHARS: {len(document_text)}")
    print(f"TOTAL CHUNKS: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"CHUNK {i}: {len(chunk)} chars")
    print("===================================")

    results = []
    for index, chunk in enumerate(chunks, 1):
        results.append(_generate_one(chunk, index, len(chunks)))

    merged = _merge_results(results)
    print("========== QWEN MERGED RESULT ==========")
    print(f"TOTAL PROGRAMS: {len(merged['programs'])}")
    print("========================================")
    return merged
