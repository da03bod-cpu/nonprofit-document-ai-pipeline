# Qwen path fix

Production flow:
- DOCX -> python-docx -> Qwen3-8B + LoRA -> JSON
- PDF -> PaddleOCR-VL -> Qwen3-8B + LoRA -> JSON
- JSON -> parser -> Qwen3-8B + LoRA -> JSON

The DOCX deterministic table bypass was removed. Long documents are handled
internally in multiple Qwen extraction passes and merged conservatively.

Useful environment variables:
- QWEN_CHUNK_CHARS=35000
- MAX_INPUT_CHARS=120000
- MAX_NEW_TOKENS=8192
- DO_SAMPLE=false
