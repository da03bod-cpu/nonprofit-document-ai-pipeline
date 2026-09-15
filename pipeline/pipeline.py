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


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".json"}


def _extension_from_name(name):
    if not name:
        return ""
    return Path(str(name)).suffix.lower()


def _extension_from_content_type(content_type):
    ct = (content_type or "").lower().split(";")[0].strip()

    if ct == "application/pdf":
        return ".pdf"

    if ct in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }:
        return ".docx"

    if ct in {
        "application/json",
        "text/json",
    }:
        return ".json"

    return ""


def _extension_from_magic(data):
    if data.startswith(b"%PDF"):
        return ".pdf"

    # DOCX is a ZIP container.
    if data.startswith(b"PK"):
        return ".docx"

    stripped = data.lstrip()
    if stripped.startswith(b"{") or stripped.startswith(b"["):
        return ".json"

    return ""


def _download(url, file_name=None):
    url_suffix = _extension_from_name(urlparse(url).path)
    name_suffix = _extension_from_name(file_name)

    # Prefer the original filename coming from n8n/Google Drive.
    suffix = name_suffix if name_suffix in SUPPORTED_EXTENSIONS else url_suffix

    fd, path = tempfile.mkstemp(suffix=suffix if suffix else ".bin")
    os.close(fd)

    try:
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()

        # If extension is still unknown, use Content-Type.
        if suffix not in SUPPORTED_EXTENSIONS:
            suffix = _extension_from_content_type(
                r.headers.get("content-type", "")
            )

        # Read enough data to identify common document formats.
        first_chunk = next(r.iter_content(1024 * 1024), b"")

        if suffix not in SUPPORTED_EXTENSIONS:
            suffix = _extension_from_magic(first_chunk)

        if suffix not in SUPPORTED_EXTENSIONS:
            ct = r.headers.get("content-type", "")
            raise ValueError(
                f"Unsupported document type. "
                f"file_name={file_name!r}, "
                f"content_type={ct!r}"
            )

        # Rename temporary file to the detected extension.
        final_path = path
        if not path.endswith(suffix):
            final_path = path + suffix

        if final_path != path:
            os.replace(path, final_path)
            path = final_path

        with open(path, "wb") as f:
            if first_chunk:
                f.write(first_chunk)

            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

        return path

    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


def process_request(job_input):
    if not isinstance(job_input, dict):
        raise ValueError("input must be a JSON object.")

    url = (
        job_input.get("file_url")
        or job_input.get("url")
        or job_input.get("document_url")
    )

    if not url:
        raise ValueError("Missing file_url.")

    file_name = (
        job_input.get("file_name")
        or job_input.get("filename")
        or job_input.get("name")
    )

    path = _download(url, file_name=file_name)

    try:
        kind = detect_document_type(path)

        if kind == "pdf":
            text = ocr_pdf(path)
        else:
            text = parse_document(path, kind)

        if not text.strip():
            raise ValueError("No usable document text was extracted.")

        text = text[:MAX_INPUT_CHARS]

        result = validate_output(
            generate_structured(text)
        )

        # Return the final schema directly under the RunPod output.
        # This makes output.programs available to n8n.
        if not isinstance(result, dict):
            raise ValueError("Model output must be a JSON object.")

        if "programs" not in result:
            raise ValueError(
                "Model output is missing the 'programs' field."
            )

        return {
            "success": True,
            "document_type": kind,
            "programs": result["programs"],
        }

    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
