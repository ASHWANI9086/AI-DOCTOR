# 🩺 VisionaryCare — Production Deployment Guide

> Deploy like a real engineer: Docker + Nginx on your own VPS.

---

## Architecture

```
User Browser
     │
     ▼ HTTP :80
  [Nginx]  ◄── reverse proxy, security headers, WebSocket upgrade
     │
     ▼ :7860 (internal Docker network only)
 [Gradio App]  ◄── Python, Groq AI, gTTS
     │
  [Docker Compose]  ◄── orchestrates both containers
     │
  [Linux VPS]  ◄── your server (AWS, DigitalOcean, Hetzner, Vultr…)
```

---

## Step 1 — Get a VPS

Pick any provider. Minimum spec: **1 vCPU, 1 GB RAM, 20 GB SSD, Ubuntu 22.04**.

| Provider | Plan | Cost | Notes |
|----------|------|------|-------|
| **AWS EC2** | t2.micro | Free (12 months) | Most professional |
| **DigitalOcean** | Basic Droplet | $6/mo | Easiest UI |
| **Hetzner** | CX22 | €4/mo | Best value |
| **Vultr** | Cloud Compute | $6/mo | Global |
| **Linode** | Nanode | $5/mo | Reliable |

### AWS EC2 Quick Start
1. Go to [AWS Console](https://console.aws.amazon.com/ec2)
2. **Launch Instance** → Ubuntu 22.04 LTS → t2.micro (free tier)
3. Create/select a key pair (`.pem` file) — keep it safe!
4. Security Group → Allow **SSH (22)**, **HTTP (80)**, **HTTPS (443)**
5. Launch → note your **Public IPv4 address**

---

## Step 2 — SSH Into Your Server

```bash
# From your Windows machine (PowerShell or WSL)
ssh -i your-key.pem ubuntu@YOUR_VPS_IP

# DigitalOcean / Hetzner / Vultr (usually password-based or SSH key)
ssh root@YOUR_VPS_IP
```

---

## Step 3 — Upload the Project

**Option A — Git (recommended)**
```bash
# On the VPS
sudo apt-get install -y git
git clone https://github.com/YOUR_USERNAME/AI-DOCTOR.git
cd AI-DOCTOR
```

**Option B — SCP from your Windows machine**
```powershell
# From PowerShell on your local machine
scp -i your-key.pem -r "C:\Users\ashwani\Downloads\AI-DOCTOR" ubuntu@YOUR_VPS_IP:~/AI-DOCTOR
ssh -i your-key.pem ubuntu@YOUR_VPS_IP
cd ~/AI-DOCTOR
```

**Option C — rsync (fastest for large projects)**
```bash
rsync -avz --exclude 'venv' --exclude '*.mp3' \
  -e "ssh -i your-key.pem" \
  "C:/Users/ashwani/Downloads/AI-DOCTOR/" \
  ubuntu@YOUR_VPS_IP:~/AI-DOCTOR/
```

---

## Step 4 — Configure API Keys

```bash
# On the VPS, inside the AI-DOCTOR directory
nano .env
```

Add your keys:
```env
GROQ_API_KEY=gsk_your_actual_groq_key_here
ELEVENLABS_API_KEY=sk_your_elevenlabs_key_here
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

> ⚠️ **Security**: The `.env` file is in `.dockerignore` and `.gitignore` — it NEVER gets into the Docker image or git history. API keys stay on the server only.

---

## Step 5 — Deploy (One Command)

```bash
# Make executable and run
chmod +x deploy.sh
sudo ./deploy.sh
```

The script will:
- ✅ Install Docker & Docker Compose
- ✅ Validate your API keys
- ✅ Configure the firewall (UFW)
- ✅ Build the Docker image (~3-5 min first time)
- ✅ Start Nginx + Gradio containers
- ✅ Print your live URL

---

## Step 6 — Access Your App

```
http://YOUR_VPS_IP
```

That's it. Your AI Doctor is live on the internet. 🎉

---

## Useful Operations

```bash
# Live logs from all containers
docker compose logs -f

# App logs only
docker compose logs -f ai-doctor

# Nginx logs only
docker compose logs -f nginx

# Container status
docker compose ps

# Restart everything
docker compose restart

# Stop everything
docker compose down

# Update app after code changes
git pull
docker compose up --build -d
```

---

## Step 7 — Add HTTPS / SSL (Optional but Recommended)

If you have a domain name (e.g. `aidoctor.yourdomain.com`):

### 7a. Point your domain to the VPS IP
Add an **A record**: `aidoctor.yourdomain.com → YOUR_VPS_IP`

### 7b. Install Certbot on the VPS
```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone \
  --non-interactive \
  --agree-tos \
  --email your@email.com \
  -d aidoctor.yourdomain.com
```

### 7c. Update nginx.conf
Uncomment the HTTPS server block and replace `your-domain.com` with your actual domain.

### 7d. Update docker-compose.yml
Uncomment the `443:443` port and the Let's Encrypt volume mounts.

### 7e. Restart
```bash
docker compose up -d
```

### 7f. Auto-renew SSL
```bash
# Add to crontab (auto-renews every 60 days)
echo "0 12 * * * root certbot renew --quiet && docker compose restart nginx" \
  | sudo tee /etc/cron.d/certbot-renew
```

---

## Monitoring

```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory
free -h
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `port 80 already in use` | `sudo systemctl stop apache2` or `sudo systemctl stop nginx` |
| App container keeps restarting | `docker compose logs ai-doctor` — check for missing API keys |
| Can't connect to site | Check VPS firewall/security group allows port 80 |
| 502 Bad Gateway | Nginx started before Gradio was ready — wait 60s and refresh |
| Audio not playing | Browser must be HTTPS for microphone access; use text input instead |
