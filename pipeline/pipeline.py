import os
import tempfile
from pathlib import Path
from urllib.request import urlopen

from config import MAX_INPUT_CHARS
from pipeline.document_parser import parse_document
from pipeline.ocr import ocr_pdf
from pipeline.qwen import generate
from pipeline.router import detect_type
from pipeline.validator import parse_model_output

def download_file(url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    if suffix not in {".pdf", ".docx", ".json"}:
        raise ValueError("file_url must point to a .pdf, .docx, or .json file")

    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    with urlopen(url, timeout=120) as response, open(path, "wb") as out:
        out.write(response.read())

    return path

def process_file(file_url: str) -> dict:
    file_path = download_file(file_url)

    try:
        source_type = detect_type(file_path)

        if source_type == "pdf":
            content = ocr_pdf(file_path)["full_text"]
        else:
            content = parse_document(file_path, source_type)

        if not content.strip():
            raise ValueError("No usable document content was extracted")

        content = content[:MAX_INPUT_CHARS]
        raw_output = generate(content)
        final_json = parse_model_output(raw_output)

        return {
            "status": "COMPLETED",
            "source_type": source_type,
            "result": final_json,
        }
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass
