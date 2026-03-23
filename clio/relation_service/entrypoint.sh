#!/bin/bash
set -e

echo "==> Waiting for database..."
until python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'relation_service.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; do
    echo "    Database not ready, retrying in 2s..."
    sleep 2
done
echo "    Database ready."

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Starting Gunicorn..."
exec gunicorn relation_service.asgi:application \
    -w 2 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:3002
