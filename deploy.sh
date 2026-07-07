#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  deploy.sh — One-command production deployment for VisionaryCare
#  Tested on: Ubuntu 22.04 / 24.04, Debian 12
#
#  Usage:
#    chmod +x deploy.sh
#    ./deploy.sh
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()    { echo -e "${GREEN}[✔]${NC} $1"; }
warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
error()  { echo -e "${RED}[✘]${NC} $1"; exit 1; }
header() { echo -e "\n${BLUE}══════════════════════════════════════${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}══════════════════════════════════════${NC}\n"; }

# ── Step 1: Check OS ──────────────────────────────────────────────────
header "VisionaryCare AI Doctor — Production Deployment"

if [[ "$EUID" -ne 0 ]]; then
    error "Please run as root: sudo ./deploy.sh"
fi

OS=$(. /etc/os-release && echo "$ID")
log "Detected OS: $OS"

# ── Step 2: Install Docker ────────────────────────────────────────────
header "Step 1/5: Installing Docker"

if command -v docker &>/dev/null; then
    log "Docker already installed: $(docker --version)"
else
    warn "Docker not found. Installing..."
    apt-get update -q
    apt-get install -y -q ca-certificates curl gnupg lsb-release

    # Official Docker install script (most reliable)
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    log "Docker installed successfully"
fi

# Install Docker Compose plugin
if ! docker compose version &>/dev/null; then
    warn "Docker Compose plugin not found. Installing..."
    apt-get install -y -q docker-compose-plugin
    log "Docker Compose installed"
else
    log "Docker Compose already installed: $(docker compose version --short)"
fi

# ── Step 3: Check .env ────────────────────────────────────────────────
header "Step 2/5: Checking Environment"

if [[ ! -f ".env" ]]; then
    warn ".env file not found! Creating template..."
    cat > .env << 'EOF'
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
EOF
    error "Please edit .env with your real API keys, then re-run this script."
fi

# Validate keys are not placeholders
if grep -q "your_groq_api_key_here" .env; then
    error "Please replace 'your_groq_api_key_here' in .env with your real GROQ API key."
fi

log ".env file looks good"

# ── Step 4: Configure firewall ────────────────────────────────────────
header "Step 3/5: Configuring Firewall"

if command -v ufw &>/dev/null; then
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    # Block direct access to Gradio port (Nginx proxies it)
    ufw deny 7860/tcp
    log "UFW firewall configured: 22 (SSH), 80, 443 open. Port 7860 internal only."
else
    warn "UFW not found — skipping firewall setup. Manually ensure only ports 22, 80, 443 are open."
fi

# ── Step 5: Build and start containers ────────────────────────────────
header "Step 4/5: Building & Starting Containers"

log "Stopping any running containers..."
docker compose down --remove-orphans 2>/dev/null || true

log "Building Docker image (this may take 3-5 minutes on first run)..."
docker compose build --no-cache

log "Starting services..."
docker compose up -d

# ── Step 6: Health check ──────────────────────────────────────────────
header "Step 5/5: Verifying Deployment"

log "Waiting for app to become healthy (up to 90 seconds)..."
MAX_WAIT=90
ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    STATUS=$(docker compose ps --format json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        s = json.loads(line)
        if s.get('Service') == 'ai-doctor':
            print(s.get('Health', 'unknown'))
    except: pass
" 2>/dev/null || echo "unknown")

    if [[ "$STATUS" == "healthy" ]]; then
        log "App container is healthy!"
        break
    fi

    echo -n "."
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo ""

# Final status
VPS_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "your-vps-ip")

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🩺 VisionaryCare is LIVE!                   ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  URL:  http://${VPS_IP}                 ║${NC}"
echo -e "${GREEN}║                                              ║${NC}"
echo -e "${GREEN}║  Useful commands:                            ║${NC}"
echo -e "${GREEN}║  docker compose logs -f     # live logs      ║${NC}"
echo -e "${GREEN}║  docker compose ps          # status         ║${NC}"
echo -e "${GREEN}║  docker compose restart     # restart        ║${NC}"
echo -e "${GREEN}║  docker compose down        # stop           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
