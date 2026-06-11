"""
NetWatch AI — Application Configuration
Pydantic BaseSettings for type-safe environment variable loading.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All application configuration loaded from environment variables."""

    # ── Deployment Profile ────────────────────
    NETWATCH_PROFILE: str = "standard"  # minimal | standard | full

    # ── Network ───────────────────────────────
    CAPTURE_INTERFACE: str = "eth0"
    SCAN_SUBNET: str = "192.168.1.0/24"

    # ── Security ──────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_ME_GENERATE_A_RANDOM_64_CHAR_HEX_STRING"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # ── Initial Admin ─────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "CHANGE_ME_USE_A_STRONG_PASSWORD"
    ADMIN_EMAIL: str = "admin@localhost"

    # ── Database ──────────────────────────────
    SQLITE_DB_PATH: str = "/app/data/netwatch.db"
    SQLITE_CACHE_SIZE_MB: int = 64

    # ── Redis ─────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_MAX_MEMORY: str = "50mb"

    # ── NATS ──────────────────────────────────
    NATS_URL: str = "nats://nats:4222"

    # ── CoreDNS ───────────────────────────────
    COREDNS_UPSTREAM_1: str = "1.1.1.1"
    COREDNS_UPSTREAM_2: str = "8.8.8.8"
    BLOCKLIST_UPDATE_INTERVAL_HOURS: int = 24

    # ── WireGuard ─────────────────────────────
    WG_SERVER_PORT: int = 51820
    WG_SERVER_ADDRESS: str = "10.8.0.1/24"
    WG_ENDPOINT: str = "auto"

    # ── ML ────────────────────────────────────
    ML_ENABLED: bool = True
    ML_ANOMALY_THRESHOLD: float = -0.2
    ML_RETRAIN_INTERVAL_HOURS: int = 24
    THREAT_INTEL_UPDATE_HOURS: int = 6

    # ── Data Retention ────────────────────────
    FLOW_RETENTION_DAYS: int = 90
    DNS_RETENTION_DAYS: int = 90
    ALERT_RETENTION_DAYS: int = 365

    # ── Frontend ──────────────────────────────
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_WS_URL: str = "ws://localhost:8000"

    # ── GeoIP ─────────────────────────────────
    MAXMIND_LICENSE_KEY: str = ""

    model_config = {"env_file": ["../.env", ".env"], "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
