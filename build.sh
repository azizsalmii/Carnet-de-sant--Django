#!/usr/bin/env bash
set -o errexit  # exit on first error

python -m pip install --upgrade pip

# Use minimal requirements for production (no heavy ML libs to avoid OOM)
if [ -f requirements_minimal.txt ]; then
  echo "Installing minimal requirements (no ML) to avoid OOM on free tier..."
  pip install -r requirements_minimal.txt
else
  echo "Installing full requirements..."
  pip install -r requirements.txt
fi

# Optional AI deps only if enabled
if [ "$ENABLE_AI_ROUTES" = "1" ] && [ -f requirements_ai.txt ]; then
  echo "ENABLE_AI_ROUTES=1, installing AI dependencies..."
  pip install -r requirements_ai.txt
else
  echo "Skipping AI dependencies (ENABLE_AI_ROUTES not set or = 0)"
fi

# Django collect static & migrate
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Optional: auto-create superuser if vars are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  python manage.py createsuperuser --noinput || true
fi
