# 🚀 ngrok Quick Start Guide

## Prerequisites

1. **Install ngrok:**
   - Download: https://ngrok.com/download
   - Extract to a folder in your PATH
   - Sign up: https://dashboard.ngrok.com/signup
   - Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
   - Configure: `ngrok config add-authtoken YOUR_TOKEN_HERE`

2. **Verify installation:**
   ```bash
   ngrok --version
   ```

## 🎯 Quick Start (2 Minutes)

### Option 1: Using Startup Script (Easiest)

**Terminal 1 - Django Server:**
```bash
# Windows CMD
start_ngrok.bat

# OR Windows PowerShell
.\start_ngrok.ps1
```

**Terminal 2 - ngrok Tunnel:**
```bash
ngrok http 8000
```

### Option 2: Manual Setup

**Terminal 1 - Django Server:**
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # PowerShell
# OR
venv\Scripts\activate.bat    # CMD

# Set environment variables
$env:NGROK="true"            # PowerShell
set NGROK=true               # CMD

# Run Django
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - ngrok Tunnel:**
```bash
ngrok http 8000
```

## 📊 What You'll See

### Terminal 1 (Django):
```
System check identified no issues (0 silenced).
October 30, 2025 - 10:30:00
Django version 5.2.7, using settings 'projetPython.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

### Terminal 2 (ngrok):
```
ngrok

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234-5678.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

## 🌐 Access Your App

**Public URL:** Copy the `Forwarding` URL from ngrok output
- Example: `https://abcd-1234-5678.ngrok-free.app`
- Share this URL with anyone!
- Works on any device (phone, tablet, etc.)

**Web Interface:** http://127.0.0.1:4040
- Inspect all HTTP requests
- Replay requests for testing
- See headers, body, response times

## ✅ Test Your App

1. **Homepage:** `https://your-ngrok-url.ngrok-free.app/`
2. **Admin:** `https://your-ngrok-url.ngrok-free.app/admin/`
3. **Login:** `https://your-ngrok-url.ngrok-free.app/reco/login/`
4. **Journal:** `https://your-ngrok-url.ngrok-free.app/journal/`
5. **Recommendations:** `https://your-ngrok-url.ngrok-free.app/reco/recommendations/`
6. **Mental Health:** `https://your-ngrok-url.ngrok-free.app/mental/`

## 🎨 Features Enabled with ngrok

✅ **All AI Models Work** (runs locally on your PC):
- Full PyTorch models (chest X-ray, brain tumor)
- Hugging Face transformers (mental health chatbot)
- ML personalization (recommendations)
- Anomaly detection

✅ **Your Local Database** (SQLite):
- All your existing data
- No migration needed
- Persistent across restarts

✅ **Quick Sharing**:
- Share with friends/clients instantly
- Test on mobile devices
- Webhook testing (payment gateways, APIs)

## 🔧 Advanced Configuration

### Custom Subdomain (Requires ngrok Pro)
```bash
ngrok http 8000 --subdomain=carnet-sante
# URL: https://carnet-sante.ngrok-free.app
```

### Reserve Fixed URL (Requires ngrok Pro)
1. Go to: https://dashboard.ngrok.com/cloud-edge/domains
2. Click "New Domain"
3. Use: `ngrok http 8000 --domain=your-fixed-url.ngrok-free.app`

### ngrok Configuration File
Create `~/.ngrok2/ngrok.yml`:
```yaml
version: "2"
authtoken: YOUR_TOKEN_HERE
tunnels:
  django:
    proto: http
    addr: 8000
    inspect: true
    schemes:
      - https
```

Run with: `ngrok start django`

## 🛡️ Security Notes

⚠️ **Important:**
- ngrok exposes your LOCAL machine to the internet
- Free tier shows "ngrok warning page" before first visit (visitors must click "Visit Site")
- Don't expose sensitive data in DEBUG mode
- Use for testing/demos only, not production

**Safe Settings Enabled:**
- `DEBUG=False` by default with ngrok (hides debug info)
- `ALLOWED_HOSTS=['*']` (required for dynamic ngrok URLs)
- `CSRF_TRUSTED_ORIGINS` configured for ngrok domains
- SSL security disabled (ngrok handles HTTPS)

## 📱 Mobile Testing

1. Start Django + ngrok (as above)
2. Copy ngrok URL from terminal
3. Open on your phone's browser
4. Test responsive design, touch interactions

## 🐛 Troubleshooting

### "ngrok not found"
```bash
# Download and install ngrok from https://ngrok.com/download
# Add to PATH or place in project directory
```

### "ERROR: Invalid Host header"
```bash
# Make sure NGROK=true is set
# Check settings.py has IS_NGROK configuration
echo $env:NGROK  # Should show "true"
```

### "CSRF verification failed"
```bash
# Clear browser cookies
# Make sure CSRF_TRUSTED_ORIGINS includes ngrok domains
# Check settings.py line ~167
```

### "Port 8000 already in use"
```bash
# Kill existing Django process:
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use different port:
python manage.py runserver 0.0.0.0:8001
ngrok http 8001
```

## 🔄 Stopping the Servers

1. **Django:** Press `Ctrl+C` in Terminal 1
2. **ngrok:** Press `Ctrl+C` in Terminal 2
3. Both will stop gracefully

## 📊 Monitoring & Debugging

**ngrok Web Interface** (http://127.0.0.1:4040):
- Real-time request inspection
- Request replay functionality
- Performance metrics
- Response analysis

**Django Debug Toolbar** (in browser):
- SQL queries
- Template rendering
- Cache hits/misses
- Signal handlers

## 🎯 When to Use ngrok

✅ **Perfect for:**
- Quick demos to clients
- Mobile device testing
- Webhook testing (Stripe, PayPal, etc.)
- Sharing work with remote team
- Testing integrations
- Short-term testing (hours)

❌ **Not suitable for:**
- Production hosting
- Long-term availability (>24 hours)
- High traffic applications
- When you need persistent URLs (unless paid plan)

## 🚀 Next Steps

**For Production Deployment, Use:**
1. **Render** - For scalable production apps
2. **PythonAnywhere** - For simple Python hosting
3. **Heroku/Railway** - For full-featured hosting

**This ngrok setup is perfect for:**
- Development testing
- Client presentations
- Mobile testing
- Quick demos

---

## 💡 Pro Tips

1. **Keep ngrok running** - URL stays same during session
2. **Use ngrok Web UI** - Great for debugging requests
3. **Share URL cautiously** - Anyone can access while tunnel is open
4. **Test webhooks** - Perfect for payment gateway testing
5. **Mobile testing** - Test your app on real devices easily

---

## 📞 Need Help?

- **ngrok Docs:** https://ngrok.com/docs
- **Django Settings:** See `projetPython/settings.py` (lines 22-41, 167-185)
- **Startup Scripts:** `start_ngrok.bat` or `start_ngrok.ps1`

**Ready to share your app with the world? Just run the commands above!** 🎉
