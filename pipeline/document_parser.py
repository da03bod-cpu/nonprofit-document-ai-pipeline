from docx import Document
from docx.document import Document as _Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
import json


def iter_block_items(parent):
    """
    Iterate through paragraphs and tables in their actual
    document order.
    """

    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._tc

    for child in parent_elm.iterchildren():

        if isinstance(child, CT_P):
            yield Paragraph(child, parent)

        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def parse_docx(file_path):
    """
    Parse a DOCX file while preserving the original order
    of paragraphs and tables.
    """

    doc = Document(file_path)

    chunks = []

    for block in iter_block_items(doc):

        # -------------------------
        # Paragraph
        # -------------------------
        if isinstance(block, Paragraph):

            text = block.text.strip()

            if text:
                chunks.append(text)

        # -------------------------
        # Table
        # -------------------------
        elif isinstance(block, Table):

            rows = []

            for row in block.rows:

                cells = [
                    cell.text.strip().replace("\n", " ")
                    for cell in row.cells
                ]

                # Ignore completely empty rows
                if any(cells):
                    rows.append(" | ".join(cells))

            if rows:

                chunks.append("===== TABLE =====")

                chunks.extend(rows)

    return "\n".join(chunks).strip()


def parse_json(file_path):
    """
    Parse JSON file and return it as formatted text.
    """

    with open(file_path, "r", encoding="utf-8") as f:

        return json.dumps(
            json.load(f),
            ensure_ascii=False,
            indent=2
        )


def parse_document(file_path, document_type):
    """
    Route the file to the correct parser.
    """

    if document_type == "docx":
        return parse_docx(file_path)

    if document_type == "json":
        return parse_json(file_path)

    raise ValueError(
        f"Unsupported parser type: {document_type}"
    )
