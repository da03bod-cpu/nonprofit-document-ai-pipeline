import json

def parse_json(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False, indent=2)

def parse_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    parts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))

    return "\n".join(parts)

def parse_document(file_path: str, source_type: str) -> str:
    if source_type == "json":
        return parse_json(file_path)
    if source_type == "docx":
        return parse_docx(file_path)
    raise ValueError(f"Unsupported document type: {source_type}")
