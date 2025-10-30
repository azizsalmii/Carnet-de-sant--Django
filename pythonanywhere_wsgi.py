"""
WSGI configuration for PythonAnywhere deployment.

INSTRUCTIONS:
1. Copy this file content to your PythonAnywhere WSGI configuration
2. Replace 'yourusername' with your actual PythonAnywhere username
3. Update paths to match your project location
"""

import os
import sys

# ========================================
# REPLACE 'yourusername' WITH YOUR ACTUAL USERNAME
# ========================================
username = 'yourusername'  # ⚠️ CHANGE THIS!

# Add your project directory to the sys.path
project_home = f'/home/{username}/Carnet-de-sante-Django'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['PYTHONANYWHERE_DOMAIN'] = f'{username}.pythonanywhere.com'
os.environ['PYTHONANYWHERE_SITE'] = 'true'
os.environ['DJANGO_SETTINGS_MODULE'] = 'projetPython.settings'

# Optionally set these:
# os.environ['SECRET_KEY'] = 'your-secret-key-here'
# os.environ['DEBUG'] = 'False'
# os.environ['ENABLE_HF_MODELS'] = '0'  # Disable heavy Hugging Face models

# Activate your virtual environment
activate_this = f'/home/{username}/.virtualenvs/carnet_env/bin/activate_this.py'
try:
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})
except FileNotFoundError:
    # Virtual environment not found - you'll need to create it
    # Run: mkvirtualenv --python=/usr/bin/python3.10 carnet_env
    pass

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
