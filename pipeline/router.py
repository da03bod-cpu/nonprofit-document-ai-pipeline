from pathlib import Path

def detect_document_type(file_path):
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".docx", ".doc"}:
        return "docx"
    if suffix == ".json":
        return "json"
    raise ValueError(f"Unsupported document type '{suffix}'. Supported: PDF, DOCX, JSON.")
