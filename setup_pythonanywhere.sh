#!/bin/bash
# PythonAnywhere Setup Script
# Run this in PythonAnywhere Bash console after cloning the repo

echo "🚀 Setting up Carnet-de-santé Django on PythonAnywhere..."
echo ""

# Get username
echo "Enter your PythonAnywhere username:"
read USERNAME

# Navigate to project
cd ~/Carnet-de-sante-Django || exit 1

# Activate virtual environment
echo "📦 Activating virtual environment..."
workon carnet_env

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies (this may take 5-10 minutes)..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create necessary directories
echo "📂 Creating media directories..."
mkdir -p media/avatars
mkdir -p media/diagnoses
mkdir -p media/diagnostics

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 ~/Carnet-de-sante-Django
chmod 755 media
chmod 755 media/avatars
chmod 755 media/diagnoses
chmod 755 media/diagnostics

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create superuser: python manage.py createsuperuser"
echo "2. Configure WSGI file in Web tab (see PYTHONANYWHERE_DEPLOYMENT.md)"
echo "3. Set static files mapping in Web tab:"
echo "   /static/ → /home/$USERNAME/Carnet-de-sante-Django/staticfiles/"
echo "   /media/  → /home/$USERNAME/Carnet-de-sante-Django/media/"
echo "4. Reload web app"
echo ""
echo "🎉 Your site will be live at: https://$USERNAME.pythonanywhere.com"
