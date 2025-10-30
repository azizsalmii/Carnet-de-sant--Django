# 🚀 Quick Start: Deploy to PythonAnywhere in 15 Minutes

## 1️⃣ Create Account (2 minutes)
1. Go to https://www.pythonanywhere.com
2. Sign up (free tier is fine)
3. Choose username (e.g., `azizsalmi`)
4. Verify email

## 2️⃣ Setup Project (5 minutes)

Open **Bash console** from Dashboard:

```bash
# Clone repository
git clone https://github.com/azizsalmii/Carnet-de-sant--Django.git
cd Carnet-de-sant--Django

# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 carnet_env

# Install dependencies (takes 5-10 min)
pip install --upgrade pip
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py createsuperuser  # Enter username, email, password
python manage.py collectstatic --noinput

# Create media directories
mkdir -p media/avatars media/diagnoses media/diagnostics
```

## 3️⃣ Configure Web App (5 minutes)

Go to **Web** tab:

### A. Add New Web App
- Click "Add a new web app"
- Choose "Manual configuration"
- Select Python 3.10

### B. Set Paths

**Source code:**
```
/home/yourusername/Carnet-de-sante-Django
```

**Virtual environment:**
```
/home/yourusername/.virtualenvs/carnet_env
```

### C. Configure WSGI

Click WSGI config file link, **DELETE ALL**, paste:

```python
import os
import sys

# ⚠️ CHANGE 'azizsalmi' TO YOUR USERNAME
username = 'azizsalmi'

project_home = f'/home/{username}/Carnet-de-sante-Django'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['PYTHONANYWHERE_DOMAIN'] = f'{username}.pythonanywhere.com'
os.environ['PYTHONANYWHERE_SITE'] = 'true'
os.environ['DJANGO_SETTINGS_MODULE'] = 'projetPython.settings'
os.environ['SECRET_KEY'] = 'your-secret-key-here-change-this'  # ⚠️ CHANGE!
os.environ['DEBUG'] = 'False'
os.environ['ENABLE_HF_MODELS'] = '0'

activate_this = f'/home/{username}/.virtualenvs/carnet_env/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Click SAVE**

### D. Static Files Mapping

In "Static files" section, add:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/Carnet-de-sante-Django/staticfiles/` |
| `/media/` | `/home/yourusername/Carnet-de-sante-Django/media/` |

**Click SAVE for each**

## 4️⃣ Launch! (1 minute)

- Scroll to top
- Click green **"Reload yourusername.pythonanywhere.com"** button
- Wait 10-20 seconds
- Visit: `https://yourusername.pythonanywhere.com`

## ✅ Success!

Your site should be live! 🎉

### Test It:
- ✅ Homepage loads
- ✅ Login works
- ✅ Admin panel: `/admin/`
- ✅ Create health journal entry
- ✅ Generate recommendations
- ✅ Feedback buttons save data

---

## 🔧 If Something Went Wrong

**Check Error Log:**
- Web tab → Click "Error log" link
- Look for Python errors

**Common fixes:**
```bash
# In Bash console:
cd ~/Carnet-de-sante-Django
workon carnet_env

# Reinstall dependencies
pip install -r requirements.txt

# Re-run migrations
python manage.py migrate

# Re-collect static files
python manage.py collectstatic --noinput

# Check permissions
chmod 755 ~/Carnet-de-sante-Django
chmod 644 db.sqlite3

# Then reload web app in Web tab
```

---

## 🔄 Update Your Site Later

```bash
# In Bash console:
cd ~/Carnet-de-sante-Django
workon carnet_env

git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Then reload in Web tab
```

---

## 📊 What Works on Free Tier

✅ **Full functionality:**
- User registration/login
- Health journal (mood tracking, daily metrics)
- AI recommendations (keyword-based, ML personalization)
- Anomaly detection
- Mental health chatbot (keyword-based)
- PDF report generation
- Feedback system for AI learning

⚠️ **Limited (dummy models):**
- Medical image analysis (chest X-ray, brain tumor)
- Heavy Hugging Face transformers

💰 **Upgrade to Hacker ($5/mo) for:**
- More CPU time (no daily limit)
- 1GB+ disk space
- Custom domain
- Ability to enable full AI models

---

## 🎯 Your URLs

| Feature | URL |
|---------|-----|
| Homepage | `https://yourusername.pythonanywhere.com/` |
| Admin | `https://yourusername.pythonanywhere.com/admin/` |
| Dashboard | `https://yourusername.pythonanywhere.com/journal/` |
| Recommendations | `https://yourusername.pythonanywhere.com/reco/recommendations/` |
| AI Diagnosis | `https://yourusername.pythonanywhere.com/ai/chest-xray/` |
| Mental Health | `https://yourusername.pythonanywhere.com/mental/` |

---

**Need detailed instructions? See `PYTHONANYWHERE_DEPLOYMENT.md`**

**Ready? Let's deploy! 🚀**
