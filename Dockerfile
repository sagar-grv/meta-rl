FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/envs:/app

COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY inference.py /app/inference.py
COPY envs /app/envs
COPY tests /app/tests

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn pydantic openai pytest

EXPOSE 7860

CMD ["uvicorn", "support_queue_env.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
