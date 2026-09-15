import os

QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "Qwen/Qwen3-8B")
LORA_PATH = os.getenv("LORA_PATH", "/app/lora-release")

MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "120000"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "8192"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
DO_SAMPLE = os.getenv("DO_SAMPLE", "false").lower() == "true"

os.environ.setdefault("HF_HOME", os.getenv("HF_HOME", "/runpod-volume/huggingface"))
os.environ.setdefault("TRANSFORMERS_CACHE", os.environ["HF_HOME"])
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
