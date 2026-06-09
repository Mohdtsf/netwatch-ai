# ── NetWatch Capture Agent ─────────────────────
FROM python:3.12-slim

# Install libpcap and network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap-dev \
    tcpdump \
    iproute2 \
    net-tools \
    arp-scan \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

# Copy source code
COPY . .

# Create data directory for GeoIP databases
RUN mkdir -p /app/data

# Run as the capture agent
CMD ["python", "-m", "src.main"]
