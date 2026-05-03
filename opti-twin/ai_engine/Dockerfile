FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt --no-deps \
    && pip install --no-cache-dir gymnasium==0.29.1 stable-baselines3==2.3.0 redis==5.0.1 pydantic==2.6.4 numpy==1.26.4 \
    && pip install --no-cache-dir anthropic==0.39.0

COPY . .

CMD ["python", "-u", "agent_service.py"]
