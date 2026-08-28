#!/bin/bash
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting web server..."
exec gunicorn --bind :${PORT:-8000} \
    --workers 1 --threads 8 --timeout 120 \
    app.main:app -k uvicorn.workers.UvicornWorker
