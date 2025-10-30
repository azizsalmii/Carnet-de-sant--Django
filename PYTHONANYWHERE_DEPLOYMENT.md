# 🚀 PythonAnywhere Deployment Guide

Complete guide to deploy your Carnet-de-santé Django application to PythonAnywhere.

---

## 📋 Prerequisites

1. **PythonAnywhere Account**: Sign up at https://www.pythonanywhere.com
   - Free tier: Basic features, 512MB disk, 100s CPU/day
   - Hacker tier ($5/mo): 1GB disk, more CPU, custom domains

2. **GitHub Repository**: Your code should be pushed to GitHub
   - Repository: `https://github.com/azizsalmii/Carnet-de-sant--Django`

---

## 🛠️ Step-by-Step Deployment

### Step 1: Create PythonAnywhere Account

1. Go to https://www.pythonanywhere.com
2. Click **"Start running Python online in less than a minute!"**
3. Choose a username (e.g., `azizsalmi`)
4. Verify your email

### Step 2: Open Bash Console

1. Login to PythonAnywhere
2. Click **"Dashboard"** → **"Consoles"** tab
3. Click **"Bash"** to open a terminal

### Step 3: Clone Your Repository

```bash
# In the PythonAnywhere Bash console:
cd ~
git clone https://github.com/azizsalmii/Carnet-de-sant--Django.git
cd Carnet-de-sant--Django
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 carnet_env

# Activate it (should auto-activate after creation)
workon carnet_env

# Verify Python version
python --version  # Should be Python 3.10.x
```

### Step 5: Install Dependencies

```bash
# Install core dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Note: Some heavy packages may be slow on free tier
# This is normal and may take 5-10 minutes
```

### Step 6: Configure Environment Variables

Create a `.env` file or set in WSGI config:

```bash
# Create .env file (optional)
nano .env
```

Add:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=False
PYTHONANYWHERE_DOMAIN=yourusername.pythonanywhere.com
ENABLE_HF_MODELS=0
```

### Step 7: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Enter username, email, password

# Collect static files
python manage.py collectstatic --noinput
```

### Step 8: Configure Web App

1. Go to **"Web"** tab in PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** (NOT Django wizard)
4. Select **Python 3.10**

#### A. Set Source Code Path

```
/home/yourusername/Carnet-de-sante-Django
```

#### B. Set Virtualenv Path

```
/home/yourusername/.virtualenvs/carnet_env
```

#### C. Configure WSGI File

Click on the WSGI configuration file link, **DELETE ALL CONTENT**, and replace with:

```python
import os
import sys

# ⚠️ REPLACE 'yourusername' WITH YOUR ACTUAL PYTHONANYWHERE USERNAME
username = 'azizsalmi'  # CHANGE THIS!

# Add project directory
project_home = f'/home/{username}/Carnet-de-sante-Django'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Environment variables
os.environ['PYTHONANYWHERE_DOMAIN'] = f'{username}.pythonanywhere.com'
os.environ['PYTHONANYWHERE_SITE'] = 'true'
os.environ['DJANGO_SETTINGS_MODULE'] = 'projetPython.settings'
os.environ['SECRET_KEY'] = 'your-secret-key-here'  # ⚠️ CHANGE THIS!
os.environ['DEBUG'] = 'False'
os.environ['ENABLE_HF_MODELS'] = '0'

# Activate virtualenv
activate_this = f'/home/{username}/.virtualenvs/carnet_env/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# Django WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Click **"Save"**

#### D. Configure Static Files

In the **"Web"** tab, scroll to **"Static files"** section:

| URL            | Directory                                                      |
|----------------|----------------------------------------------------------------|
| `/static/`     | `/home/yourusername/Carnet-de-sante-Django/staticfiles/`      |
| `/media/`      | `/home/yourusername/Carnet-de-sante-Django/media/`            |

Click **"Save"** for each entry.

### Step 9: Reload Web App

1. Scroll to top of **"Web"** tab
2. Click big green **"Reload yourusername.pythonanywhere.com"** button
3. Wait 10-20 seconds

### Step 10: Test Your Site

Visit: `https://yourusername.pythonanywhere.com`

You should see your homepage! 🎉

---

## 🔧 Troubleshooting

### Error: "Something went wrong :("

**Check Error Logs:**
1. Go to **"Web"** tab
2. Click **"Error log"** link
3. Look for Python errors

**Common Issues:**

#### 1. ImportError / ModuleNotFoundError
```bash
# In Bash console:
workon carnet_env
pip install missing-package-name
# Then reload web app
```

#### 2. Static Files Not Loading
```bash
# Run collectstatic again
cd ~/Carnet-de-sante-Django
python manage.py collectstatic --noinput

# Check static files mapping in Web tab
# Should point to: /home/username/Carnet-de-sante-Django/staticfiles/
```

#### 3. Database Errors
```bash
# Re-run migrations
python manage.py migrate --run-syncdb

# Check database file permissions
ls -la db.sqlite3
chmod 664 db.sqlite3  # If needed
```

#### 4. ALLOWED_HOSTS Error
```python
# In settings.py (should already be fixed)
ALLOWED_HOSTS = ['.pythonanywhere.com', 'yourusername.pythonanywhere.com']
```

---

## 🔄 Updating Your Deployment

When you make changes to your code:

```bash
# 1. Open Bash console
# 2. Navigate to project
cd ~/Carnet-de-sante-Django

# 3. Pull latest changes
git pull origin main

# 4. Install any new dependencies
workon carnet_env
pip install -r requirements.txt

# 5. Run migrations (if any)
python manage.py migrate

# 6. Collect static files (if changed)
python manage.py collectstatic --noinput

# 7. Reload web app
# Go to Web tab → Click "Reload"
```

---

## 📊 Performance Notes

### Free Tier Limitations

✅ **Works:**
- Homepage, dashboards, user authentication
- Health journal, recommendations (with keyword-based AI)
- Anomaly detection, mood tracking
- All CRUD operations

⚠️ **Limited:**
- AI medical image analysis (uses dummy models)
- Hugging Face transformers (disabled via ENABLE_HF_MODELS=0)
- CPU-intensive tasks (100s/day limit)

💰 **Hacker Tier ($5/month) Enables:**
- More CPU time (no daily limit)
- 1GB+ disk space
- Custom domain support
- Ability to run heavier AI models (still CPU-only, no GPU)

### Optimization Tips

1. **Keep Heavy Models Disabled** in production:
   ```python
   # In WSGI or .env
   os.environ['ENABLE_HF_MODELS'] = '0'
   ```

2. **Use Background Tasks** for long operations:
   - Set up scheduled tasks in PythonAnywhere
   - Run monthly report generation via cron

3. **Monitor CPU Usage**:
   - Check "Account" tab for CPU seconds used
   - Optimize database queries if hitting limits

---

## 🗄️ Database Options

### SQLite (Default - Free Tier)

✅ Already configured, no changes needed
⚠️ Limited to single process, good for <10k records

```python
# settings.py (current)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### MySQL (Recommended for Production)

Available on free tier, better concurrency:

1. **Create MySQL Database** in PythonAnywhere:
   - Go to "Databases" tab
   - Initialize MySQL
   - Create database: `yourusername$carnet_db`

2. **Update settings.py**:
```python
if IS_PYTHONANYWHERE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'yourusername$carnet_db'),
            'USER': os.environ.get('DB_USER', 'yourusername'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': 'yourusername.mysql.pythonanywhere-services.com',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
```

3. **Install MySQL client**:
```bash
pip install mysqlclient
```

4. **Migrate data**:
```bash
python manage.py migrate
# Or dump from SQLite and import to MySQL
```

---

## 🔐 Security Checklist

- [ ] Generate new SECRET_KEY for production
- [ ] Set DEBUG=False in WSGI config
- [ ] Verify ALLOWED_HOSTS includes your domain
- [ ] Keep .env file out of version control
- [ ] Use strong superuser password
- [ ] Enable HTTPS (automatic on PythonAnywhere)
- [ ] Set file permissions correctly:
  ```bash
  chmod 755 ~/Carnet-de-sante-Django
  chmod 644 db.sqlite3
  chmod 755 media/
  ```

---

## 📞 Support Resources

- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
- **Help Pages**: https://help.pythonanywhere.com/
- **Django Docs**: https://docs.djangoproject.com/
- **Your Project Docs**: See `.github/copilot-instructions.md`

---

## ✅ Post-Deployment Checklist

- [ ] Site loads at `https://yourusername.pythonanywhere.com`
- [ ] Static files (CSS/JS) loading correctly
- [ ] Can login to admin at `/admin/`
- [ ] User registration works
- [ ] Health journal pages accessible
- [ ] Recommendations generate successfully
- [ ] Feedback buttons save data
- [ ] PDF reports download
- [ ] Media uploads work (avatars, diagnostic images)
- [ ] No errors in error log

---

## 🎯 Quick Reference

| Task | Command/Location |
|------|------------------|
| Bash Console | Dashboard → Consoles → Bash |
| Error Logs | Web tab → Error log link |
| Reload App | Web tab → Green "Reload" button |
| View Site | `https://yourusername.pythonanywhere.com` |
| Admin Panel | `https://yourusername.pythonanywhere.com/admin/` |
| Update Code | `cd ~/Carnet-de-sante-Django; git pull` |
| Run Command | `workon carnet_env; python manage.py <command>` |

---

**🚀 You're all set! Your Django health tracking app is now live on PythonAnywhere!**

Need help? Check the error logs first, then consult PythonAnywhere forums.
