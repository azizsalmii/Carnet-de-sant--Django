#!/usr/bin/env bash
set -o errexit  # exit on first error

python -m pip install --upgrade pip

# Core deps
pip install -r requirements.txt

# Optional AI deps file (install only if present)
if [ -f requirements_ai.txt ]; then
  pip install -r requirements_ai.txt
fi

# Django collect static & migrate
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Optional: auto-create superuser if vars are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  python manage.py createsuperuser --noinput || true
fi
