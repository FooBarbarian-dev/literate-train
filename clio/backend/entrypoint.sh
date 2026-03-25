#!/bin/bash
set -e

echo "==> Waiting for database..."
until python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; do
    echo "    Database not ready, retrying in 2s..."
    sleep 2
done
echo "    Database ready."

if [ "$RUN_STARTUP_SCRIPTS" = "true" ]; then
    echo "==> Running migrations..."
    python manage.py migrate --noinput

    echo "==> Collecting static files..."
    python manage.py collectstatic --noinput --clear 2>/dev/null || true

    echo "==> Seeding initial passwords..."
    python manage.py seed_initial_passwords

    echo "==> Ensuring Django admin users exist..."
    python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

# Create admin superuser
admin_pw = os.environ.get('ADMIN_PASSWORD', '')
if admin_pw and not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', admin_pw)
    print('  Created Django superuser: admin')
elif not admin_pw:
    print('  ADMIN_PASSWORD not set, skipping admin user')
else:
    print('  Django superuser admin already exists')

# Create regular staff user (can view Django admin but not modify)
user_pw = os.environ.get('USER_PASSWORD', '')
if user_pw and not User.objects.filter(username='user').exists():
    u = User.objects.create_user('user', 'user@localhost', user_pw)
    u.is_staff = True
    u.save()
    print('  Created Django staff user: user')
elif not user_pw:
    print('  USER_PASSWORD not set, skipping regular user')
else:
    print('  Django staff user already exists')
"
fi

echo "==> Starting Gunicorn..."
exec gunicorn backend.asgi:application \
    -w ${WEB_CONCURRENCY:-2} \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:3001
