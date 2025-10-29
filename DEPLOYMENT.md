# Deployment Guide: Carnet-de-santé-Django on Render

## 🚀 Quick Deployment Steps

### 1. Prerequisites
- GitHub account with your repository: https://github.com/azizsalmii/Carnet-de-sant--Django.git
- Render account (free): https://render.com

### 2. Push Changes to GitHub

```bash
# Navigate to your project
cd "c:\Users\LM. SHOP\Desktop\Python\Carnet-de-sant--Django"

# Add all new deployment files
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 3. Deploy on Render

#### Option A: Using render.yaml (Recommended - Infrastructure as Code)

1. Go to https://render.com/dashboard
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Click **"Apply"**
6. Wait 10-15 minutes for the build (PyTorch is large)

#### Option B: Manual Setup

1. **Create PostgreSQL Database:**
   - Dashboard → New → PostgreSQL
   - Name: `carnet-de-sante-db`
   - Plan: Free
   - Create Database
   - **Copy the Internal Database URL**

2. **Create Web Service:**
   - Dashboard → New → Web Service
   - Connect repository: `azizsalmii/Carnet-de-sant--Django`
   - Name: `carnet-de-sante`
   - Runtime: **Python 3**
   - Branch: `main`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn projetPython.wsgi:application`

3. **Add Environment Variables:**
   - `SECRET_KEY`: Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG`: `False`
   - `DATABASE_URL`: Paste Internal Database URL from step 1
   - `ALLOWED_HOSTS`: Your Render URL (e.g., `carnet-de-sante.onrender.com`)
   - `PYTHON_VERSION`: `3.11.0`

4. **Deploy:**
   - Click "Create Web Service"
   - Wait 10-15 minutes for first deployment

### 4. Post-Deployment Setup

Once deployed, access your Render shell to create a superuser:

```bash
# In Render Dashboard → Shell tab
python manage.py createsuperuser
```

### 5. Access Your Application

- **Main App**: https://your-app-name.onrender.com
- **Admin Panel**: https://your-app-name.onrender.com/admin
- **Health Recommendations**: https://your-app-name.onrender.com/reco/dashboard/
- **AI Medical Analysis**: https://your-app-name.onrender.com/ai/
- **Mental Health Chat**: https://your-app-name.onrender.com/mental/

## 📋 Important Notes

### Free Tier Limitations
- **Spins down after 15 min of inactivity** (first request may be slow)
- **512 MB RAM limit** (sufficient for this app)
- **PostgreSQL free tier**: 1GB storage, deleted after 90 days of inactivity

### Large Models Warning
- **PyTorch** (2.3GB) will take 10-15 minutes to install
- **First deployment** may timeout - this is normal, let it complete
- **ML models** (.pth, .joblib files) are included in git - ensure they're not too large

### Static Files
- Handled by **WhiteNoise** (no external service needed)
- Automatically collected during build

### Media Files (User Uploads)
- **Issue**: Free tier has ephemeral storage (files deleted on redeploy)
- **Solutions**:
  1. **Cloudinary** (recommended for production): https://cloudinary.com
  2. **AWS S3** (requires setup)
  3. **Keep on Render** (for testing only)

### Model File Sizes
Check if your AI model files are within limits:

```bash
# Check model sizes
ls -lh ai_models/*.pth
ls -lh models/v1/*.joblib
ls -lh MentalHealth/ml_models/*.pkl
```

If models are **>100MB each**, consider:
1. Using Git LFS (Large File Storage)
2. Downloading models on first startup from cloud storage
3. Using quantized/smaller models

## 🔧 Troubleshooting

### Build Fails
**Problem**: Timeout during PyTorch installation
**Solution**: 
- This is normal for first build (large dependencies)
- Let it run for 15-20 minutes
- Render will retry automatically

### Static Files Not Loading
**Problem**: CSS/JS not found (404 errors)
**Solution**:
```bash
# Check build logs for "collectstatic" success
# Ensure WhiteNoise is in MIDDLEWARE (already done)
# Clear browser cache
```

### Database Connection Error
**Problem**: `OperationalError: could not connect to server`
**Solution**:
- Verify `DATABASE_URL` environment variable is set
- Use **Internal Database URL** (not External)
- Check database is running in Render dashboard

### Models Not Loading
**Problem**: `.pth` or `.joblib` file not found
**Solution**:
- Ensure model files are committed to git
- Check paths in settings: `AI_CXR_CKPT`, `AI_BRAIN_CKPT`
- Verify files exist after build in Render shell:
  ```bash
  ls -la ai_models/
  ls -la models/v1/
  ```

### Out of Memory (OOM) Error
**Problem**: App crashes with memory error
**Solution**:
- **Upgrade to paid tier** ($7/month for 512MB → 2GB)
- **Optimize model loading**: Use lazy loading, clear cache after use
- **Reduce concurrent requests**: Add rate limiting

### App URL Returns 404
**Problem**: All pages return 404
**Solution**:
- Check `ALLOWED_HOSTS` includes your Render domain
- Verify `DEBUG=False` in environment variables
- Check Django logs in Render dashboard

## 🔐 Security Checklist

✅ `DEBUG=False` in production  
✅ `SECRET_KEY` is randomly generated  
✅ `ALLOWED_HOSTS` set correctly  
✅ Database uses PostgreSQL (not SQLite)  
✅ HTTPS enforced (`SECURE_SSL_REDIRECT=True`)  
✅ CSRF and session cookies secured  
✅ WhiteNoise serving static files  

## 📊 Monitoring

Monitor your app health:
- **Render Dashboard**: CPU, Memory, Request logs
- **Django Admin**: `/admin/` for database health
- **Logs**: Real-time in Render dashboard

## 🚀 Continuous Deployment

Render auto-deploys on git push to `main`:

```bash
# Make changes
git add .
git commit -m "Your changes"
git push origin main

# Render automatically rebuilds and deploys
```

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **Issue Tracker**: Open issue on GitHub repository

---

**Estimated first deployment time**: 15-20 minutes (due to PyTorch)
**Subsequent deployments**: 5-10 minutes
