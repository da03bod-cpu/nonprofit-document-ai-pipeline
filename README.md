# Nonprofit Document AI Pipeline

Production pipeline for extracting structured program/project JSON from nonprofit reports.

## Architecture

PDF -> PaddleOCR-VL 1.6 -> Qwen3-8B + trained LoRA -> Structured JSON

DOCX -> Qwen3-8B + trained LoRA -> Structured JSON

JSON -> Qwen3-8B + trained LoRA -> Structured JSON

## Components

- `handler.py`: RunPod Serverless entrypoint.
- `pipeline/router.py`: input type detection.
- `pipeline/ocr.py`: PaddleOCR-VL 1.6 PDF OCR.
- `pipeline/document_parser.py`: DOCX and JSON parsing.
- `pipeline/qwen.py`: Qwen3-8B + PEFT LoRA inference.
- `pipeline/prompt.py`: extraction prompt.
- `pipeline/validator.py`: JSON output validation.
- `pipeline/pipeline.py`: end-to-end orchestration.

## Model

Base: `Qwen/Qwen3-8B`

LoRA source:
`da03bod-cpu/qwen3-nonprofit-training` / `lora-release`

The adapter is intentionally not copied into this repository.

## Environment

```text
QWEN_MODEL_NAME=Qwen/Qwen3-8B
LORA_REPO_ID=da03bod-cpu/qwen3-nonprofit-training
LORA_SUBFOLDER=lora-release
MAX_NEW_TOKENS=4096
MAX_INPUT_CHARS=120000
```

## Serverless input

```json
{
  "input": {
    "file_url": "https://example.com/report.pdf"
  }
}
```

The endpoint returns the final structured JSON.
