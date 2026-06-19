FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libffi-dev \
       curl \
       wget \
       libnss3 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libdrm2 \
       libxkbcommon0 \
       libxdamage1 \
       libxcomposite1 \
       libxrandr2 \
       libgbm1 \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libcairo2 \
       libasound2 \
       ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /opt/venv/bin/playwright install chromium

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libffi8 \
       libnss3 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libdrm2 \
       libxkbcommon0 \
       libxdamage1 \
       libxcomposite1 \
       libxrandr2 \
       libgbm1 \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libcairo2 \
       libasound2 \
       ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appuser \
    && adduser --system --ingroup appuser appuser

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]