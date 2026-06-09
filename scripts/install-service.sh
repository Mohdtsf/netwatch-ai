#!/usr/bin/env bash
# ══════════════════════════════════════════════
# NetWatch AI — Systemd Service Installer
# Installs and enables auto-start on boot
# Usage: sudo bash scripts/install-service.sh
# ══════════════════════════════════════════════

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_FILE="/etc/systemd/system/netwatch.service"

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root (sudo)${NC}"
    exit 1
fi

echo -e "${CYAN}Installing NetWatch AI systemd service...${NC}"

# Copy and patch the service file
cp "$SCRIPT_DIR/netwatch.service" "$SERVICE_FILE"
sed -i "s|WorkingDirectory=/opt/netwatch|WorkingDirectory=$PROJECT_DIR|g" "$SERVICE_FILE"
sed -i "s|EnvironmentFile=/opt/netwatch/.env|EnvironmentFile=$PROJECT_DIR/.env|g" "$SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

# Enable auto-start
systemctl enable netwatch.service

echo -e "${GREEN}✅ NetWatch service installed${NC}"
echo ""
echo "  Start now:          sudo systemctl start netwatch"
echo "  Check status:       sudo systemctl status netwatch"
echo "  View logs:          sudo journalctl -u netwatch -f"
echo "  Disable auto-start: sudo systemctl disable netwatch"
echo ""
