# 🚀 Render Deployment Checklist

## Pre-Deployment

- [ ] Read `DEPLOY_QUICKSTART.md` for overview
- [ ] Ensure all ML model files are committed to git (check sizes with `ls -lh`)
- [ ] GitHub repository is up to date

## Step 1: Push to GitHub

Run these commands:

```bash
cd "c:\Users\LM. SHOP\Desktop\Python\Carnet-de-sant--Django"

# Add deployment files
git add .
git commit -m "Add Render production deployment configuration"
git push origin main
```

## Step 2: Sign Up & Connect Render

- [ ] Go to https://render.com and sign up (free)
- [ ] Connect your GitHub account
- [ ] Authorize access to `azizsalmii/Carnet-de-sant--Django` repo

## Step 3: Deploy (Choose ONE method)

### Method A: Blueprint (Recommended - Easiest)

- [ ] Dashboard → **New** → **Blueprint**
- [ ] Select repository: `azizsalmii/Carnet-de-sant--Django`
- [ ] Render detects `render.yaml`
- [ ] Click **Apply**
- [ ] Wait 15-20 minutes for build

### Method B: Manual Setup (More Control)

#### 3a. Create PostgreSQL Database
- [ ] Dashboard → **New** → **PostgreSQL**
- [ ] Name: `carnet-de-sante-db`
- [ ] Region: Choose closest to you
- [ ] Plan: **Free**
- [ ] Click **Create Database**
- [ ] **COPY the Internal Database URL** (starts with `postgresql://`)

#### 3b. Create Web Service
- [ ] Dashboard → **New** → **Web Service**
- [ ] Connect repository: `azizsalmii/Carnet-de-sant--Django`
- [ ] Name: `carnet-de-sante` (or your preferred name)
- [ ] Runtime: **Python 3**
- [ ] Branch: `main`
- [ ] Build Command: `./build.sh`
- [ ] Start Command: `gunicorn projetPython.wsgi:application`
- [ ] Plan: **Free**

#### 3c. Add Environment Variables

In the web service settings → Environment:

```
SECRET_KEY = j2k5z%2rc97*fphc%qgz(f!r#euw+aj04gzpk$i87x&@!23lya
# ☝️ Use the one generated above or generate new with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

DEBUG = False

DATABASE_URL = <paste Internal Database URL from step 3a>
# Example: postgresql://carnet_user:xxxxx@dpg-xxxxx/carnet_de_sante

ALLOWED_HOSTS = your-app-name.onrender.com
# Replace with your actual Render URL (you'll see it after creating service)

PYTHON_VERSION = 3.11.0
```

- [ ] Add all environment variables above
- [ ] Click **Create Web Service**
- [ ] Wait 15-20 minutes for first build

## Step 4: Post-Deployment Setup

Once deployment succeeds:

- [ ] Copy your app URL: `https://your-app-name.onrender.com`
- [ ] Go to Render Dashboard → your service → **Shell** tab
- [ ] Run: `python manage.py createsuperuser`
- [ ] Create admin user (username, email, password)

## Step 5: Test Your App

Visit these URLs and verify everything works:

- [ ] `https://your-app-name.onrender.com/` - Home page loads
- [ ] `https://your-app-name.onrender.com/admin/` - Admin panel accessible
- [ ] `https://your-app-name.onrender.com/reco/dashboard/` - Recommendations
- [ ] `https://your-app-name.onrender.com/ai/` - AI Medical Analysis
- [ ] `https://your-app-name.onrender.com/mental/` - Mental Health Chat
- [ ] Create test user and verify signup/login works
- [ ] Upload test image to verify media handling
- [ ] Add health metrics and generate recommendations

## Step 6: Monitor & Maintain

- [ ] Bookmark Render Dashboard for monitoring
- [ ] Check logs if any issues: Dashboard → your service → **Logs** tab
- [ ] Set up email/Slack notifications in Render settings (optional)
- [ ] Note: Free tier spins down after 15 min inactivity (first load will be slow)

## Troubleshooting

### Build Fails with Timeout
- **Expected!** First build takes 15-20 min due to PyTorch (2.3GB)
- Let it run, Render will retry automatically
- Check build logs for actual errors

### Static Files Not Loading (404 on CSS/JS)
- WhiteNoise should handle this automatically
- Clear browser cache
- Verify `STATIC_ROOT` has files: check Shell → `ls staticfiles/`

### Database Connection Error
- Verify `DATABASE_URL` environment variable is set correctly
- Must use **Internal Database URL** (not External)
- Format: `postgresql://user:pass@host:5432/dbname`

### App Shows "Not Found" (404)
- Check `ALLOWED_HOSTS` includes your Render domain
- Verify domain matches exactly (e.g., `my-app.onrender.com`)
- Check Django logs in Render dashboard

### Out of Memory (OOM) Crash
- Free tier has 512MB RAM - tight with PyTorch + Transformers
- **Solution 1**: Upgrade to paid tier ($7/month = 2GB RAM)
- **Solution 2**: Optimize model loading (lazy loading, clear cache)
- **Solution 3**: Disable less-critical ML features

### Uploaded Images Disappear After Redeploy
- **Expected!** Free tier has ephemeral storage
- **Solution**: Integrate Cloudinary (free tier available)
- See `DEPLOYMENT.md` for Cloudinary setup instructions

## Additional Resources

- `DEPLOY_QUICKSTART.md` - Quick overview
- `DEPLOYMENT.md` - Comprehensive guide with troubleshooting
- `.env.example` - Environment variables template
- Render Docs: https://render.com/docs/deploy-django
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/

## Need Help?

- Check Render logs: Dashboard → Service → Logs
- Review Django settings: `projetPython/settings.py`
- Test locally first: `python manage.py runserver`
- Open GitHub issue on your repo for community support

---

**Estimated Total Time**: 25-30 minutes (first deployment)

**Your SECRET_KEY (generated)**:
```
j2k5z%2rc97*fphc%qgz(f!r#euw+aj04gzpk$i87x&@!23lya
```
*(Use this or generate a new one)*
