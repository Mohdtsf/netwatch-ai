#!/usr/bin/env bash
# ══════════════════════════════════════════════
# NetWatch AI — One-Command Remote Bootstrapper
# Usage: curl -fsSL https://raw.githubusercontent.com/Mohdtsf/netwatch-ai/main/scripts/bootstrap.sh | bash
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
echo "║       NetWatch AI — Bootstrapper         ║"
echo "║   Autonomous Network Security System     ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── Function: Install Git ─────────────────────
check_and_install_git() {
    if ! command -v git &>/dev/null; then
        echo -e "${YELLOW}Git is not installed on this system.${NC}"
        echo -e "Attempting to install git using package manager..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update && sudo apt-get install -y git
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y git
        elif command -v yum &>/dev/null; then
            sudo yum install -y git
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm git
        else
            echo -e "${RED}Error: Could not auto-detect package manager to install Git.${NC}"
            echo -e "Please install git manually and rerun this command."
            exit 1
        fi
        echo -e "${GREEN}✓ Git installed successfully.${NC}\n"
    fi
}

# ── Main Entry ────────────────────────────────

# Check and install git
check_and_install_git

# Detect environment and pull or clone the repository
if [ -d .git ] && git remote -v 2>/dev/null | grep -q "netwatch-ai"; then
    echo -e "${CYAN}Running inside NetWatch directory. Checking for updates...${NC}"
    git pull
    echo -e "${GREEN}✓ Up to date.${NC}\n"
    chmod +x netwatch
    ./netwatch
else
    if [ -d "netwatch-ai" ]; then
        echo -e "${CYAN}Found existing netwatch-ai folder. Entering and checking for updates...${NC}"
        cd netwatch-ai
        git pull
        echo -e "${GREEN}✓ Up to date.${NC}\n"
        chmod +x netwatch
        ./netwatch
    else
        echo -e "${CYAN}Cloning NetWatch AI repository...${NC}"
        git clone https://github.com/Mohdtsf/netwatch-ai.git netwatch-ai
        cd netwatch-ai
        echo -e "${GREEN}✓ Cloned successfully.${NC}\n"
        chmod +x netwatch
        ./netwatch
    fi
fi
