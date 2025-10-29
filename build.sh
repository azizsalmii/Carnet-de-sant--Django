#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements_prod.txt

# Download NLTK data (for MentalHealth app)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
