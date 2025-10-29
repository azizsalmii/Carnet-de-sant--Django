# Quick Deploy to Render

## ✨ What's Been Set Up

Your Django health app is now **production-ready** for Render deployment! Here's what was configured:

### 📦 Files Created

1. **`requirements_prod.txt`** - Unified production dependencies (Django, PyTorch, ML libs, PostgreSQL)
2. **`build.sh`** - Automated build script (installs deps, collects static, migrates DB)
3. **`render.yaml`** - Infrastructure as Code (defines web service + PostgreSQL)
4. **`Procfile`** - Backup process definition for Render
5. **`runtime.txt`** - Python 3.11.0 specification
6. **`.env.example`** - Environment variable template
7. **`DEPLOYMENT.md`** - Complete deployment guide with troubleshooting

### 🔧 Settings Updated (`projetPython/settings.py`)

- ✅ **Environment-based configuration** (SECRET_KEY, DEBUG, DATABASE_URL from env vars)
- ✅ **PostgreSQL support** with `dj-database-url` (auto-switches between SQLite dev / PostgreSQL prod)
- ✅ **WhiteNoise middleware** for static file serving (no external CDN needed)
- ✅ **Security headers** enabled in production (HTTPS, HSTS, secure cookies)
- ✅ **ALLOWED_HOSTS** includes `.onrender.com` wildcard

## 🚀 Deploy Steps (5 minutes)

### 1. Commit & Push

```bash
cd "c:\Users\LM. SHOP\Desktop\Python\Carnet-de-sant--Django"

# Stage deployment files
git add .github/copilot-instructions.md .env.example build.sh DEPLOYMENT.md Procfile render.yaml requirements_prod.txt runtime.txt projetPython/settings.py

# Commit
git commit -m "Add Render deployment configuration

- Add production requirements with PostgreSQL, gunicorn, whitenoise
- Configure environment-based settings (SECRET_KEY, DATABASE_URL)
- Add build script for automated deployment
- Enable WhiteNoise for static files
- Add security headers for production
- Create comprehensive deployment guide"

# Push to GitHub
git push origin main
```

### 2. Deploy on Render

**Go to**: https://render.com/dashboard

**Option A - Automatic (Recommended):**
1. New → **Blueprint**
2. Connect repo: `azizsalmii/Carnet-de-sant--Django`
3. Click **Apply** (render.yaml detected automatically)
4. Wait ~15 minutes (PyTorch is large)

**Option B - Manual:**
1. New → **PostgreSQL** → Name: `carnet-de-sante-db` → Create
2. New → **Web Service** → Connect repo
3. Build Command: `./build.sh`
4. Start Command: `gunicorn projetPython.wsgi:application`
5. Add Environment Variables:
   - `SECRET_KEY`: (generate with Python: `from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())`)
   - `DEBUG`: `False`
   - `DATABASE_URL`: (from PostgreSQL internal connection string)
   - `ALLOWED_HOSTS`: `your-app.onrender.com`

### 3. Post-Deployment

```bash
# In Render Shell (dashboard → your service → Shell tab)
python manage.py createsuperuser
```

### 4. Test Your App

- Main: `https://your-app.onrender.com`
- Admin: `https://your-app.onrender.com/admin`
- Recommendations: `https://your-app.onrender.com/reco/dashboard/`
- AI Medical: `https://your-app.onrender.com/ai/`
- Mental Health: `https://your-app.onrender.com/mental/`

## ⚠️ Important Notes

### Free Tier Limits
- App **spins down after 15 min inactivity** (first load = slow)
- **512 MB RAM** (sufficient but tight with PyTorch)
- **PostgreSQL**: 1GB, deleted after 90 days inactivity

### Build Time
- **First deploy**: 15-20 minutes (PyTorch is 2.3GB)
- **Subsequent**: 5-10 minutes (cached)

### Media Files Issue
Free tier has **ephemeral storage** - uploaded images (avatars, diagnostics) **deleted on redeploy**.

**Solutions:**
1. **Cloudinary** (free tier: https://cloudinary.com) - recommended
2. **AWS S3** - requires setup
3. **Accept limitation** for testing only

### Large Model Files
Your AI models (`.pth`, `.joblib`, `.pkl`) should be in git. If any file >100MB:
- Use **Git LFS** (Large File Storage)
- Or download models on startup from cloud storage

Check sizes:
```bash
ls -lh ai_models/*.pth
ls -lh models/v1/*.joblib
ls -lh MentalHealth/ml_models/*.pkl
```

## 🐛 Common Issues

**Build timeout?** → Normal for first deploy (PyTorch). Let it run 20 minutes.

**Static files 404?** → Clear browser cache, verify WhiteNoise in MIDDLEWARE.

**Database error?** → Use **Internal Database URL** (not External) in env vars.

**Out of memory?** → Upgrade to $7/month tier (512MB → 2GB RAM).

**App returns 404?** → Check `ALLOWED_HOSTS` includes your Render domain.

## 📖 Full Documentation

See `DEPLOYMENT.md` for:
- Detailed troubleshooting
- Security checklist
- Monitoring tips
- Continuous deployment setup

## 🎉 You're Ready!

Your Django health app with AI models is configured for production deployment on Render without Docker!
