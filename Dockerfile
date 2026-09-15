FROM ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest-nvidia-gpu

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HF_HUB_DISABLE_XET=1 \
    HF_HOME=/runpod-volume/huggingface \
    TRANSFORMERS_CACHE=/runpod-volume/huggingface

RUN apt-get update && \
    apt-get install -y --no-install-recommends git git-lfs ca-certificates && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    "torch==2.6.0" --index-url https://download.pytorch.org/whl/cu124 && \
    python -m pip install --no-cache-dir \
    "transformers>=4.51.0" \
    "peft>=0.15.0" \
    "bitsandbytes>=0.45.0" \
    "accelerate>=1.6.0" \
    "python-docx>=1.1.2" \
    "requests>=2.32.0" \
    "runpod>=1.7.0"

RUN rm -rf /tmp/qwen3-training /app/lora-release && \
    git clone --depth 1 --branch main \
      https://github.com/da03bod-cpu/qwen3-nonprofit-training.git \
      /tmp/qwen3-training && \
    test -f /tmp/qwen3-training/lora-release/adapter_model.safetensors && \
    mkdir -p /app/lora-release && \
    cp -a /tmp/qwen3-training/lora-release/. /app/lora-release/ && \
    rm -rf /tmp/qwen3-training

COPY config.py handler.py requirements.txt ./
COPY pipeline/ ./pipeline/

CMD ["python", "-u", "handler.py"]
