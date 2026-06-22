# NetWatch AI

> **Self-hosted network security platform** — live traffic monitoring, DNS firewall, packet firewall, device tracker, WireGuard VPN, AI anomaly detection — all from one web dashboard.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Next.js](https://img.shields.io/badge/next.js-15-black)

---

## What It Does

- **Captures** all network traffic through your router (passive monitoring)
- **Identifies** every device on your network by MAC, IP, hostname, and type
- **Tracks** what websites and apps every device visits (via DNS + TLS SNI)
- **Blocks** malware domains, ads, and specific websites via DNS firewall
- **Enforces** packet-level firewall rules via nftables
- **Runs** a self-hosted WireGuard VPN with QR code provisioning
- **Detects** anomalies and threats via ML (Isolation Forest + Random Forest)
- **Alerts** in real time with optional auto-blocking

## Quick Start

### One-Command Setup & Run
Run the following command in your terminal to automatically pull, install, configure, and start NetWatch with a clean, interactive dashboard:
```bash
curl -fsSL https://raw.githubusercontent.com/Mohdtsf/netwatch-ai/main/scripts/bootstrap.sh | bash
```

### Local Setup
Alternatively, if you already have the repository cloned:
```bash
# Enter project directory
cd netwatch

# Run the interactive manager (auto-installs Docker and configures settings if missing)
./netwatch
```

**Dashboard:** http://localhost:3000  
**API Docs:** http://localhost:8000/docs

## Architecture

```
Internet → Router → Capture Agent (Scapy)
                         ↓
                   NATS JetStream
                    ↙    ↓    ↘
              FastAPI   ML    Redis
                ↓     Engine
           SQLite (WAL)
                ↓
         CoreDNS + nftables + WireGuard
                ↓
           Nginx → Next.js Dashboard
```

## Resource Profiles

| Profile | RAM | ML | Target |
|---------|-----|----|--------|
| `minimal` | 512 MB | ❌ | Raspberry Pi 3, old laptops |
| `standard` | 600 MB | ✅ | Any 2015+ laptop |
| `full` | 1.2 GB | ✅ + MLflow | Dedicated machines |

```bash
# Start with specific profile
PROFILE=minimal make up
PROFILE=full make up
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) |
| Capture | Scapy + libpcap |
| Messaging | NATS JetStream |
| Database | SQLite (WAL mode) |
| ML | scikit-learn (Isolation Forest, Random Forest, HDBSCAN) |
| DNS Firewall | CoreDNS |
| Packet Firewall | nftables |
| VPN | WireGuard |
| Frontend | Next.js 15 + TypeScript |
| Proxy | Nginx |
| Cache | Redis 7 |

## Commands

```bash
make help           # Show all commands
make up             # Start all services
make down           # Stop all services
make logs           # Follow logs
make status         # Show service status
make test           # Run all tests
make lint           # Lint all Python code
make health         # Check service health
make db-upgrade     # Run database migrations
make shell-backend  # Shell into backend container
```

## Deployment Modes

### Tier 1 — Zero Config (30 seconds)
Plug in, see your own traffic and all devices on the network.

### Tier 2 — DNS Guardian (5 minutes)
Change your router's DNS server to your laptop's IP. Network-wide ad/malware blocking.

### Tier 3 — Full Guardian (15 minutes)
Add a USB ethernet adapter. Full packet capture and firewall control for all devices.

## Development

```bash
# Backend (FastAPI)
cd backend && pip install -e ".[dev]"
uvicorn src.main:app --reload

# Frontend (Next.js)
cd frontend && npm install
npm run dev
```

## License

MIT
