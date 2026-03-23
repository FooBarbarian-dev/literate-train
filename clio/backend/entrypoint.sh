#!/bin/bash
set -e

echo "==> Waiting for database..."
until python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
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

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

echo "==> Seeding initial passwords..."
python manage.py seed_initial_passwords

echo "==> Ensuring Django admin superuser exists..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
pw = os.environ.get('ADMIN_PASSWORD', '')
if pw and not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', pw)
    print('  Created Django admin superuser (username: admin)')
else:
    print('  Superuser already exists or ADMIN_PASSWORD not set')
"

echo "==> Starting Gunicorn..."
exec gunicorn backend.asgi:application \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:3001
