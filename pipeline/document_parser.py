import json
from docx import Document

def parse_docx(file_path):
    doc = Document(file_path)
    chunks = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            chunks.append(text)

    for i, table in enumerate(doc.tables, 1):
        chunks.append(f"===== TABLE {i} =====")
        for row in table.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            chunks.append(" | ".join(cells))

    return "\n".join(chunks).strip()

def parse_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.dumps(json.load(f), ensure_ascii=False, indent=2)

def parse_document(file_path, document_type):
    if document_type == "docx":
        return parse_docx(file_path)
    if document_type == "json":
        return parse_json(file_path)
    raise ValueError(f"Unsupported parser type: {document_type}")
