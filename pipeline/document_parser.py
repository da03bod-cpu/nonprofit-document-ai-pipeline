from docx import Document
from docx.document import Document as _Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
import json


def iter_block_items(parent):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\r", " ").replace("\t", " ")
    return " ".join(text.split()).strip()


def parse_table(table):
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            cell_text = (cell.text or "").replace("\n", " ").replace("\r", " ")
            cells.append(clean_text(cell_text))
        if any(cells):
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def parse_docx(file_path):
    doc = Document(file_path)
    chunks = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = clean_text(block.text)
            if text:
                chunks.append(text)
        elif isinstance(block, Table):
            table_text = parse_table(block)
            if table_text:
                chunks.extend(["===== TABLE START =====", table_text, "===== TABLE END ====="])
    return "\n".join(chunks).strip()


def parse_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False, indent=2)


def parse_document(file_path, document_type):
    document_type = document_type.lower().strip()
    if document_type == "docx":
        return parse_docx(file_path)
    if document_type == "json":
        return parse_json(file_path)
    raise ValueError(f"Unsupported parser type: {document_type}")
