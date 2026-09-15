import json
from paddleocr import PaddleOCRVL

_pipeline = None

def get_ocr_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = PaddleOCRVL()
    return _pipeline

def _raw_json(result):
    raw = getattr(result, "json", result)
    if isinstance(raw, str):
        raw = json.loads(raw)
    return raw

def _blocks(result):
    raw = _raw_json(result)
    if not isinstance(raw, dict):
        return []

    data = raw.get("data", raw)
    res = data.get("res", data) if isinstance(data, dict) else data
    if not isinstance(res, dict):
        return []

    for key in ("parsing_res_list", "blocks", "ocr_res", "results"):
        value = res.get(key)
        if isinstance(value, list):
            return value
    return []

def _text(block):
    if not isinstance(block, dict):
        return ""
    for key in ("block_content", "text", "content"):
        value = block.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

def ocr_pdf(file_path):
    results = get_ocr_pipeline().predict(file_path)
    pages = []

    for page_number, result in enumerate(results, 1):
        texts = [_text(b) for b in _blocks(result)]
        texts = [t for t in texts if t]
        if texts:
            page_text = "\n".join(texts)
        else:
            page_text = str(_raw_json(result))

        pages.append(f"===== PAGE {page_number} =====\n{page_text}")

    return "\n\n".join(pages).strip()
