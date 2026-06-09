#!/usr/bin/env bash
# ══════════════════════════════════════════════
# NetWatch AI — One-Command Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
# Or:    bash scripts/install.sh
# ══════════════════════════════════════════════

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║       NetWatch AI — Installer            ║"
echo "║  Self-hosted network security platform   ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── Check Prerequisites ───────────────────────

check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        echo "  Install it: $2"
        exit 1
    else
        echo -e "${GREEN}✓${NC} $1 found"
    fi
}

echo -e "${BOLD}Checking prerequisites...${NC}"
check_command "docker" "https://docs.docker.com/get-docker/"
check_command "docker" "https://docs.docker.com/compose/install/"
check_command "git" "sudo apt install git"
echo ""

# Check Docker is running
if ! docker info &>/dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "  Start it: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker daemon running"

# Check Docker Compose v2
if ! docker compose version &>/dev/null; then
    echo -e "${RED}✗ Docker Compose v2 not found${NC}"
    echo "  Install: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose v2 found"
echo ""

# ── Create .env if not exists ─────────────────

if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env

    # Generate random JWT secret
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    sed -i "s/CHANGE_ME_GENERATE_A_RANDOM_64_CHAR_HEX_STRING/$JWT_SECRET/" .env

    echo -e "${GREEN}✓${NC} .env created with random JWT secret"
    echo -e "${YELLOW}⚠  Edit .env to set your admin password and network interface${NC}"
else
    echo -e "${GREEN}✓${NC} .env already exists"
fi

# ── Detect Network Interface ─────────────────

echo ""
echo -e "${BOLD}Available network interfaces:${NC}"
ip -br link show | grep -v "lo " | awk '{printf "  %-20s %s\n", $1, $2}'
echo ""

DEFAULT_IF=$(ip route show default 2>/dev/null | awk '{print $5}' | head -1)
if [ -n "$DEFAULT_IF" ]; then
    echo -e "  Default interface: ${CYAN}$DEFAULT_IF${NC}"
    sed -i "s/CAPTURE_INTERFACE=eth0/CAPTURE_INTERFACE=$DEFAULT_IF/" .env
fi

# ── Detect Subnet ─────────────────────────────

DEFAULT_SUBNET=$(ip -4 addr show "$DEFAULT_IF" 2>/dev/null | grep -oP 'inet \K[\d.]+/\d+' | head -1)
if [ -n "$DEFAULT_SUBNET" ]; then
    # Convert to .0/24 network
    NETWORK=$(echo "$DEFAULT_SUBNET" | sed 's/\.[0-9]*\//.0\//')
    echo -e "  Default subnet:    ${CYAN}$NETWORK${NC}"
    sed -i "s|SCAN_SUBNET=192.168.1.0/24|SCAN_SUBNET=$NETWORK|" .env
fi

# ── Create data directories ──────────────────

echo ""
echo -e "${BOLD}Creating data directories...${NC}"
mkdir -p data/ml-models
echo -e "${GREEN}✓${NC} Data directories ready"

# ── Select Profile ────────────────────────────

echo ""
echo -e "${BOLD}Select resource profile:${NC}"
echo "  1) minimal  — 512 MB RAM, no ML (old laptops, Pi 3)"
echo "  2) standard — 600 MB RAM, full features (default)"
echo "  3) full     — 1.2 GB RAM, MLflow tracking"
echo ""
read -p "Profile [2]: " PROFILE_CHOICE
PROFILE_CHOICE=${PROFILE_CHOICE:-2}

case $PROFILE_CHOICE in
    1)
        PROFILE="minimal"
        COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.minimal.yml"
        ;;
    3)
        PROFILE="full"
        COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.full.yml"
        ;;
    *)
        PROFILE="standard"
        COMPOSE_CMD="docker compose"
        ;;
esac

sed -i "s/NETWATCH_PROFILE=standard/NETWATCH_PROFILE=$PROFILE/" .env
echo -e "${GREEN}✓${NC} Profile set to: $PROFILE"

# ── Build & Start ─────────────────────────────

echo ""
echo -e "${BOLD}Building and starting NetWatch AI...${NC}"
echo -e "${YELLOW}This may take a few minutes on first run.${NC}"
echo ""

$COMPOSE_CMD build
$COMPOSE_CMD up -d

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ NetWatch AI is running!            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Dashboard:  ${CYAN}http://localhost:3000${NC}"
echo -e "  API:        ${CYAN}http://localhost:8000${NC}"
echo -e "  API Docs:   ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  Profile:    ${CYAN}$PROFILE${NC}"
echo ""
echo -e "  Manage with: ${BOLD}make help${NC}"
echo ""
