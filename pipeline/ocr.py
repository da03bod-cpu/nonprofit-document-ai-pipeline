from functools import lru_cache
from paddleocr import PaddleOCRVL

@lru_cache(maxsize=1)
def get_ocr():
    return PaddleOCRVL()

def ocr_pdf(file_path: str) -> dict:
    pipeline = get_ocr()
    results = pipeline.predict(file_path)

    pages = []
    all_text = []

    for result in results:
        raw = result.json if hasattr(result, "json") else None
        page_text = ""

        if isinstance(raw, dict):
            page_text = raw.get("text", "") or ""

        page_no = len(pages) + 1
        pages.append({
            "page": page_no,
            "text": page_text,
            "raw": raw,
        })

        if page_text:
            all_text.append(f"===== PAGE {page_no} =====\n{page_text}")

    return {
        "source_type": "pdf",
        "pages": pages,
        "full_text": "\n\n".join(all_text),
    }
