from pathlib import Path

SUPPORTED = {".pdf": "pdf", ".docx": "docx", ".json": "json"}

def detect_type(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported: {', '.join(SUPPORTED)}"
        )
    return SUPPORTED[suffix]
