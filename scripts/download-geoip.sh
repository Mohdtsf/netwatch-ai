#!/usr/bin/env bash
# ══════════════════════════════════════════════
# Download MaxMind GeoLite2 databases
# Requires: MAXMIND_LICENSE_KEY in .env
# ══════════════════════════════════════════════

set -euo pipefail

if [ -z "${MAXMIND_LICENSE_KEY:-}" ]; then
    echo "⚠️  MAXMIND_LICENSE_KEY not set"
    echo "   Sign up at: https://www.maxmind.com/en/geolite2/signup"
    echo "   Then set MAXMIND_LICENSE_KEY in your .env file"
    exit 1
fi

DATA_DIR="data"
mkdir -p "$DATA_DIR"

echo "Downloading GeoLite2-City..."
curl -fsSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=$MAXMIND_LICENSE_KEY&suffix=tar.gz" \
    | tar xz --strip-components=1 -C "$DATA_DIR" --wildcards '*.mmdb'

echo "Downloading GeoLite2-ASN..."
curl -fsSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=$MAXMIND_LICENSE_KEY&suffix=tar.gz" \
    | tar xz --strip-components=1 -C "$DATA_DIR" --wildcards '*.mmdb'

echo "✅ GeoIP databases downloaded to $DATA_DIR/"
ls -lh "$DATA_DIR"/*.mmdb
