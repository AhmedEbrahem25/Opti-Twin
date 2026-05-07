FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install torch from the CPU-only wheel index first to avoid pulling CUDA.
# requirements.txt also pins torch==2.2.2 -- pip will see it satisfied and skip.
# torch is a ~750 MB wheel; raise the per-request timeout and retry count so
# a slow connection doesn't fail the whole build.
ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=5
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command runs the live recommendation service. The `trainer` compose
# service overrides this with `python <train_*>.py` for one-shot training.
CMD ["python", "-u", "agent_service.py"]
