import os

QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "Qwen/Qwen3-8B")
LORA_REPO_ID = os.getenv(
    "LORA_REPO_ID",
    "da03bod-cpu/qwen3-nonprofit-training",
)
LORA_SUBFOLDER = os.getenv("LORA_SUBFOLDER", "lora-release")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "4096"))
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "120000"))
