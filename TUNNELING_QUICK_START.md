# Tunneling Services - Instant Remote Access (No Deployment!)

Get a public URL to your local app in seconds. Perfect for quick testing with friends without full deployment.

## Option 1: Cloudflare Tunnel (RECOMMENDED - Free & Secure)

**Pros:** Free, no rate limits, easy setup, very secure
**Cons:** Requires Cloudflare account (free)

### Setup (2 minutes)

```bash
# 1. Download cloudflared
# Windows: https://github.com/cloudflare/cloudflared/releases
# Or use: choco install cloudflare-warp
# Or: winget install Cloudflare.cloudflared

# 2. Authenticate
cloudflared tunnel login

# 3. Tunnel your backend API (runs on port 8000)
cloudflared tunnel --url http://localhost:8000

# You'll get a URL like:
# https://blah-blah-blah.trycloudflare.com
```

### In another terminal, tunnel your frontend:
```bash
# Frontend runs on 5173 or 3000 (depends on dev setup)
cloudflared tunnel --url http://localhost:5173
```

### Now you have:
- **Frontend**: `https://frontend-id.trycloudflare.com`
- **API**: `https://api-id.trycloudflare.com`

**Share these URLs with testers immediately!**

---

## Option 2: ngrok (Simple, Works Great)

**Pros:** Very simple, popular, good uptime
**Cons:** Free tier has rate limits and 2hr timeout

### Setup (3 minutes)

```bash
# 1. Sign up at https://ngrok.com
# 2. Download: https://ngrok.com/download
# Or: choco install ngrok

# 3. Add your auth token (from ngrok dashboard)
ngrok config add-authtoken YOUR_TOKEN_HERE

# 4. Expose backend (8000)
ngrok http 8000
# You get: https://abc123def456.ngrok-free.app

# 5. In another terminal, expose frontend (5173)
ngrok http 5173
# You get: https://xyz789abc123.ngrok-free.app
```

**Limitations:**
- Free tier: 2 hour session limit
- Shared domains (not custom)
- Rate limit: ~20 req/sec
- **Solution:** Upgrade to paid ($5/month) for always-on

---

## Option 3: Localtunnel (Quickest!)

**Pros:** Ultra-simple, no signup needed!
**Cons:** Less stable than others, slower

### Setup (1 minute)

```bash
# Install
npm install -g localtunnel

# Backend (8000)
lt --port 8000
# You get: https://kind-horse-56.loca.lt

# Frontend (5173)
lt --port 5173
# You get: https://smiling-panda-89.loca.lt
```

---

## Option 4: Serveo (No Installation!)

**Pros:** Works via SSH, no signup, incredibly simple
**Cons:** Less control, security depends on SSH trust

### Setup (30 seconds)

```bash
# Just this one command!
ssh -R 80:localhost:8000 serveo.net
# You get: https://[random-id].serveo.net
```

---

## Recommended Setup for Testing

### You (Developer)
```powershell
# Terminal 1: Frontend dev server
cd sports-prediction-platform/frontend
npm run dev
# Running on http://localhost:5173

# Terminal 2: Backend API
cd sports-prediction-platform/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Running on http://localhost:8000

# Terminal 3: Tunnel frontend (Cloudflare)
cloudflared tunnel --url http://localhost:5173
# Returns: https://frontend-tunnel-id.trycloudflare.com

# Terminal 4: Tunnel API (Cloudflare)
cloudflared tunnel --url http://localhost:8000
# Returns: https://api-tunnel-id.trycloudflare.com
```

### Tell Your Testers
```
✅ App is ready to test!

Frontend: https://frontend-tunnel-id.trycloudflare.com
API: https://api-tunnel-id.trycloudflare.com

Just open the frontend link and start testing!
```

---

## Fix API URL for Tunneling

Your frontend needs to know where the API is.

### Option A: Update Environment Variable

Edit `.env` in frontend folder:
```
VITE_API_URL=https://api-tunnel-id.trycloudflare.com
```

Then restart frontend dev server.

### Option B: Quick Fix (Temporary)

Edit `frontend/src/utils/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api-tunnel-id.trycloudflare.com/api';
```

---

## Comparison: Which Service to Use?

| Service | Cost | Setup Time | Stability | Rate Limit | Best For |
|---------|------|-----------|-----------|-----------|----------|
| **Cloudflare** ⭐ | Free | 2 min | Excellent | None | Production testing |
| **ngrok** | Free (limited) | 3 min | Very Good | 20 req/sec | Quick demos |
| **Localtunnel** | Free | 1 min | Good | Unknown | Rapid prototyping |
| **Serveo** | Free | 30 sec | Fair | Unknown | Emergency access |

**Recommended: Cloudflare Tunnel** (free, unlimited, most reliable)

---

## Common Issues & Fixes

### "Connection refused" / "Cannot connect to backend"
```
Problem: Frontend trying to reach API at wrong URL
Solution: Update VITE_API_URL to match your tunnel API URL
```

### "Cloudflared not found"
```bash
# Reinstall
choco uninstall cloudflare-warp
choco install cloudflare-warp

# Or download manually from:
# https://github.com/cloudflare/cloudflared/releases
```

### "ngrok: command not found"
```bash
# Download from https://ngrok.com/download
# Extract and add to PATH
# Or: choco install ngrok
```

### "401 Unauthorized" on ngrok
```bash
# Your auth token expired or wrong
ngrok config add-authtoken YOUR_NEW_TOKEN
```

### "Too many requests" (rate limited)
```
Problem: Free tier hitting rate limits
Solution: 
  - Use Cloudflare instead (no rate limits)
  - Upgrade ngrok to paid ($5/month)
  - Delay between test requests
```

---

## Sharing with Multiple Testers

All testers use **the same URL** you share:

```
Send this to all testers:
https://your-frontend-tunnel.trycloudflare.com

All testers click that link → They see your app!
```

They can:
- ✅ Browse predictions
- ✅ Create accounts
- ✅ Test predictions
- ✅ All simultaneously!

---

## Keep Tunnels Running

**Important:** Keep terminal windows open while tunneling!

```
❌ Don't close this:
cloudflared tunnel --url http://localhost:5173

✅ Keep it open = Tunnel stays active
```

When you close the terminal → Tunnel dies → URL no longer works

**Pro tip:** Use `screen` or `tmux` to keep processes running in background
```bash
# Linux/Mac
screen -S tunnel
cloudflared tunnel --url http://localhost:8000
# Press Ctrl+A then D to detach
screen -r tunnel  # Resume later

# Windows: Use separate PowerShell windows or use "Start-Job"
Start-Job { cloudflared tunnel --url http://localhost:8000 }
```

---

## Security Note

⚠️ **Public URL = Anyone Can Access**

Tunneling makes your local app public! This is fine for testing, but:

✅ **OK to share:**
- Frontend URL (public-facing anyway)
- API URL (your testers need it)

❌ **Never share:**
- Database password (in env file, not in tunnel)
- Admin credentials
- Sensitive test data

**Good practice:**
- Use temporary test accounts
- Disable payment processing for testing
- Review logs for suspicious activity
- Take tunnel down when done testing

---

## Quick Command Cheat Sheet

```bash
# Cloudflare
cloudflared tunnel --url http://localhost:8000
cloudflared tunnel --url http://localhost:5173

# ngrok  
ngrok http 8000
ngrok http 5173

# Localtunnel
lt --port 8000
lt --port 5173

# Serveo
ssh -R 80:localhost:8000 serveo.net
ssh -R 80:localhost:5173 serveo.net
```

---

## Next Steps

1. **Choose a service** (Cloudflare recommended)
2. **Install tunneling tool**
3. **Start your app locally** (frontend + backend)
4. **Run tunnel command** in new terminal
5. **Get public URL**
6. **Share with testers**
7. **They click link and test!**

**Done! 🎉 Your app is accessible from anywhere.**

---

## When Testing is Done

```bash
# Press Ctrl+C in tunnel terminal to stop
# URL dies immediately
# Your local app still runs fine
```

---

## Want Permanent Testing?

If tunnels aren't persistent enough, use permanent deployment:
- **Quick:** Railway.app (see QUICK_DEPLOYMENT.md)
- **Self-hosted:** Docker with own server
- See PRODUCTION_DEPLOYMENT_GUIDE.md

But for **quick, immediate testing?** Tunnels are perfect! 🚀
