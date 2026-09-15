import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from config import MAX_INPUT_CHARS
from pipeline.document_parser import parse_document
from pipeline.ocr import ocr_pdf
from pipeline.qwen import generate_structured
from pipeline.router import detect_document_type
from pipeline.validator import validate_output

def _download(url):
    suffix = Path(urlparse(url).path).suffix.lower()
    fd, path = tempfile.mkstemp(suffix=suffix if suffix else ".bin")
    os.close(fd)

    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()

    if suffix not in {".pdf", ".docx", ".doc", ".json"}:
        ct = r.headers.get("content-type", "").lower()
        if "pdf" in ct:
            new_suffix = ".pdf"
        elif "officedocument" in ct or "word" in ct:
            new_suffix = ".docx"
        elif "json" in ct:
            new_suffix = ".json"
        else:
            os.unlink(path)
            raise ValueError(f"Unsupported content type: {ct}")
        new_path = path + new_suffix
        os.replace(path, new_path)
        path = new_path

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)
    return path

def process_request(job_input):
    if not isinstance(job_input, dict):
        raise ValueError("input must be a JSON object.")

    url = job_input.get("file_url") or job_input.get("url") or job_input.get("document_url")
    if not url:
        raise ValueError("Missing file_url.")

    path = _download(url)
    try:
        kind = detect_document_type(path)
        text = ocr_pdf(path) if kind == "pdf" else parse_document(path, kind)
        if not text.strip():
            raise ValueError("No usable document text was extracted.")

        text = text[:MAX_INPUT_CHARS]
        result = validate_output(generate_structured(text))

        return {"success": True, "document_type": kind, "result": result}
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
