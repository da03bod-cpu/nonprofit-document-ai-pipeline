from docx import Document
from docx.document import Document as _Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

import json


def iter_block_items(parent):
    """
    Iterate through paragraphs and tables in their original
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


def clean_text(text):
    """
    Clean unnecessary whitespace while preserving Arabic text.
    """

    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    # Remove duplicated spaces
    text = " ".join(text.split())

    return text.strip()


def parse_table(table):
    """
    Convert a Word table into readable text while preserving
    row and column structure.
    """

    rows = []

    for row in table.rows:

        cells = []

        for cell in row.cells:

            cell_text = cell.text.strip()

            # Preserve line breaks inside cells
            cell_text = cell_text.replace("\n", " ")
            cell_text = cell_text.replace("\r", " ")

            cell_text = clean_text(cell_text)

            cells.append(cell_text)

        # Ignore completely empty rows
        if any(cell for cell in cells):

            row_text = " | ".join(cells)

            rows.append(row_text)

    if not rows:
        return ""

    return "\n".join(rows)


def parse_docx(file_path):
    """
    Extract text from DOCX while preserving the original
    order of paragraphs and tables.

    Example:

        Paragraph
        Paragraph
        Table
        Paragraph
        Table

    will remain in exactly that order.
    """

    doc = Document(file_path)

    chunks = []

    for block in iter_block_items(doc):

        # -----------------------------------------
        # Paragraph
        # -----------------------------------------
        if isinstance(block, Paragraph):

            text = clean_text(block.text)

            if text:
                chunks.append(text)

        # -----------------------------------------
        # Table
        # -----------------------------------------
        elif isinstance(block, Table):

            table_text = parse_table(block)

            if table_text:

                chunks.append("===== TABLE START =====")

                chunks.append(table_text)

                chunks.append("===== TABLE END =====")

    return "\n".join(chunks).strip()


def parse_json(file_path):
    """
    Read JSON file and convert it to formatted UTF-8 text.
    """

    with open(file_path, "r", encoding="utf-8") as f:

        data = json.load(f)

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


def parse_document(file_path, document_type):
    """
    Main document parser.

    Supported:
        - docx
        - json
    """

    document_type = document_type.lower().strip()

    if document_type == "docx":

        return parse_docx(file_path)

    if document_type == "json":

        return parse_json(file_path)

    raise ValueError(
        f"Unsupported parser type: {document_type}"
    )
