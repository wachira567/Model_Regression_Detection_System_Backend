# --- Stage 1: Build ---
FROM python:3.11-slim as builder
WORKDIR /build
COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir --prefix=/install .

# --- Stage 2: Production ---
FROM python:3.11-slim
RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy prompts and dataset (baked into image for CI/CD runs)
COPY prompts/ ./prompts/
COPY golden-dataset/ ./golden-dataset/

RUN mkdir -p /app/reports && chown app:app /app/reports
USER app

EXPOSE 8000
CMD alembic upgrade head && exec gunicorn --bind :${PORT:-8000} \
    --workers 1 --threads 8 --timeout 120 \
    app.main:app -k uvicorn.workers.UvicornWorker

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')"
