# 🚀 ngrok Quick Start - YOUR COMMANDS

## ✅ Setup Complete!
- ngrok installed ✓
- authtoken configured ✓
- Django configured ✓

---

## 🎯 START YOUR APP (2 Commands)

### Terminal 1 - Django Server
```powershell
.\run_django.ps1
```
**Wait for:** `Starting development server at http://0.0.0.0:8000/`

### Terminal 2 - ngrok Tunnel
```powershell
ngrok http 8000
```
**Look for:** `Forwarding  https://xxxx.ngrok-free.app -> http://localhost:8000`

---

## 🌐 Your Public URLs

After starting both terminals, you'll get:

**Main URL:** `https://xxxx-xxxx-xxxx.ngrok-free.app/`

**Key Pages:**
- Homepage: `/`
- Admin: `/admin/`
- Login: `/reco/login/`
- Dashboard: `/journal/`
- Recommendations: `/reco/recommendations/`
- AI Diagnosis: `/ai/chest-xray/`
- Mental Health: `/mental/`

**ngrok Dashboard:** http://127.0.0.1:4040 (inspect all requests)

---

## 🛑 STOP Everything

1. **Stop Django:** Press `Ctrl+C` in Terminal 1
2. **Stop ngrok:** Press `Ctrl+C` in Terminal 2

---

## 🔄 RESTART Later

Just run the same 2 commands:
```powershell
# Terminal 1
.\run_django.ps1

# Terminal 2 (new terminal)
ngrok http 8000
```

---

## 📱 Share Your App

1. Start both servers (see above)
2. Copy the ngrok URL from Terminal 2
3. Share with anyone - they can access from anywhere!

Example: `https://1234-5678-abcd.ngrok-free.app`

---

## 🐛 Troubleshooting

### "Port 8000 already in use"
```powershell
# Kill the process
netstat -ano | findstr :8000
taskkill /PID <NUMBER> /F
```

### Django won't start
```powershell
# Check if all dependencies are installed
python -m pip install -r requirements.txt
```

### ngrok shows "tunnel not found"
```powershell
# Re-add authtoken
ngrok config add-authtoken 2YqYdN34lVpj1LAcfl74vwcIqqsJJCSAN_823ih77jU2QdkHmuRmmyz
```

---

## 💡 Pro Tips

1. **Keep both terminals open** while using the app
2. **URL stays same** during the session (until you restart ngrok)
3. **First-time visitors** see ngrok warning page (click "Visit Site")
4. **ngrok Dashboard** at http://127.0.0.1:4040 shows all requests in real-time
5. **Mobile testing:** Open ngrok URL on your phone

---

## 🎉 That's It!

**Start command:** `.\run_django.ps1` + `ngrok http 8000`  
**Stop command:** `Ctrl+C` (both terminals)  
**Share URL:** Copy from ngrok terminal

Enjoy your instant public deployment! 🚀
