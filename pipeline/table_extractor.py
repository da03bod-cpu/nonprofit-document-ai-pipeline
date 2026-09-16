"""Deprecated DOCX table bypass.

The production pipeline intentionally does not call this module. DOCX is
parsed to text and sent to Qwen3-8B + LoRA so semantic fields are extracted
from the report context rather than synthesized by Python.
"""


def extract_projects_from_docx(file_path, year=None):
    return []
