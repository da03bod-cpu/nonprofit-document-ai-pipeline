# Nonprofit Document AI Pipeline

PDF -> PaddleOCR-VL 1.6 -> Qwen3-8B + trained LoRA -> structured JSON

DOCX/JSON -> parser -> Qwen3-8B + trained LoRA -> structured JSON

The trained adapter is fetched from:
`https://github.com/da03bod-cpu/qwen3-nonprofit-training`

It is copied into `/app/lora-release` during Docker build and then loaded locally by PEFT.

RunPod input:

```json
{"input":{"file_url":"https://example.com/report.pdf"}}
```

Supported: PDF, DOCX, JSON.

The Qwen base model is downloaded from Hugging Face at runtime.
