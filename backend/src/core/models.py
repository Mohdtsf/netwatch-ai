"""
NetWatch AI — SQLAlchemy Models
All database tables defined as SQLAlchemy ORM models.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(256), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(16), default="viewer")  # admin | analyst | viewer
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(32), primary_key=True, default=_uuid)
    mac_address = Column(String(17), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    hostname = Column(String(256), nullable=True)
    device_type = Column(String(32), default="unknown")  # phone | laptop | tv | iot | router | unknown
    custom_name = Column(String(256), nullable=True)
    vendor = Column(String(256), nullable=True)
    os_type = Column(String(64), nullable=True)
    first_seen = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    last_seen = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    is_blocked = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)
    vpn_enabled = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100

    # Relationships
    flows = relationship("Flow", back_populates="device", lazy="dynamic")
    alerts = relationship("Alert", back_populates="device", lazy="dynamic")
    dns_queries = relationship("DnsQuery", back_populates="device", lazy="dynamic")
    vpn_peer = relationship("VpnPeer", back_populates="device", uselist=False)

    __table_args__ = (
        Index("idx_devices_mac", "mac_address"),
        Index("idx_devices_ip", "ip_address"),
        Index("idx_devices_online", "is_online"),
    )


class Flow(Base):
    __tablename__ = "flows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer, nullable=False, index=True)
    src_ip = Column(String(45))
    dst_ip = Column(String(45))
    src_port = Column(Integer)
    dst_port = Column(Integer)
    protocol = Column(String(10))
    bytes = Column(Integer, default=0)
    packets = Column(Integer, default=0)
    domain = Column(String(256))
    country = Column(String(3))
    asn = Column(String(128))
    anomaly_score = Column(Float, default=0.0)
    threat_label = Column(String(32), default="Normal")
    device_id = Column(String(32), ForeignKey("devices.id"), nullable=True)

    device = relationship("Device", back_populates="flows")

    __table_args__ = (
        Index("idx_flows_time", "time"),
        Index("idx_flows_src", "src_ip", "time"),
        Index("idx_flows_dst", "dst_ip", "time"),
        Index("idx_flows_device", "device_id", "time"),
    )


class FlowAggregate(Base):
    """Pre-aggregated 1-minute traffic buckets."""
    __tablename__ = "flows_1min"

    bucket = Column(Integer, primary_key=True)
    src_ip = Column(String(45), primary_key=True)
    dst_ip = Column(String(45), primary_key=True)
    total_bytes = Column(Integer, default=0)
    total_packets = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_flows_1min_bucket", "bucket"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(32), primary_key=True, default=_uuid)
    time = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    severity = Column(String(16))  # low | medium | high | critical
    type = Column(String(32))  # PortScan | DDoS | BruteForce | Exfiltration | NewDevice | ThreatIntel
    message = Column(Text)
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    device_id = Column(String(32), ForeignKey("devices.id"), nullable=True)
    auto_blocked = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(32), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(Integer, nullable=True)

    device = relationship("Device", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_time", "time"),
        Index("idx_alerts_severity", "severity", "acknowledged"),
    )


class DnsQuery(Base):
    __tablename__ = "dns_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer, nullable=False)
    device_id = Column(String(32), ForeignKey("devices.id"), nullable=True)
    src_ip = Column(String(45))
    domain = Column(String(256))
    query_type = Column(String(10), default="A")  # A | AAAA | CNAME | MX | TXT
    action = Column(String(16), default="allowed")  # allowed | blocked
    category = Column(String(32))  # malware | ads | adult | tracker | custom

    device = relationship("Device", back_populates="dns_queries")

    __table_args__ = (
        Index("idx_dns_time", "time"),
        Index("idx_dns_device", "device_id", "time"),
        Index("idx_dns_domain", "domain"),
    )


class DnsRule(Base):
    __tablename__ = "dns_rules"

    id = Column(String(32), primary_key=True, default=_uuid)
    device_id = Column(String(32), ForeignKey("devices.id"), nullable=True)  # NULL = all devices
    domain_pattern = Column(String(256), nullable=False)
    action = Column(String(16), default="block")  # block | allow
    category = Column(String(32))
    created_by = Column(String(32), ForeignKey("users.id"), nullable=True)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))


class FirewallRule(Base):
    __tablename__ = "firewall_rules"

    id = Column(String(32), primary_key=True, default=_uuid)
    device_id = Column(String(32), ForeignKey("devices.id"), nullable=True)  # NULL = global
    rule_type = Column(String(16))  # ip | port | mac | rate_limit | time_based
    direction = Column(String(16))  # inbound | outbound | both
    target = Column(String(256), nullable=False)
    action = Column(String(16), default="drop")  # drop | accept | reject
    schedule = Column(String(64), nullable=True)  # cron for time-based
    enabled = Column(Boolean, default=True)
    auto_block = Column(Boolean, default=False)  # created by ML
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    expires_at = Column(Integer, nullable=True)  # auto-expire for temp blocks


class VpnPeer(Base):
    __tablename__ = "vpn_peers"

    id = Column(String(32), primary_key=True, default=_uuid)
    device_id = Column(String(32), ForeignKey("devices.id"), nullable=True)
    peer_name = Column(String(128))
    public_key = Column(String(64), nullable=False)
    private_key_enc = Column(Text, nullable=True)  # AES-encrypted
    preshared_key_enc = Column(Text, nullable=True)
    allowed_ips = Column(String(256), default="0.0.0.0/0")
    assigned_ip = Column(String(45))
    endpoint = Column(String(256), nullable=True)
    tunnel_mode = Column(String(16), default="full")  # full | split | none
    enabled = Column(Boolean, default=True)
    last_handshake = Column(Integer, nullable=True)
    rx_bytes = Column(Integer, default=0)
    tx_bytes = Column(Integer, default=0)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))

    device = relationship("Device", back_populates="vpn_peer")


class AuditLog(Base):
    """Track admin actions for security."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    user_id = Column(String(32), ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)  # login | logout | block_device | add_rule etc.
    target_type = Column(String(32))  # device | rule | user | vpn_peer
    target_id = Column(String(32))
    details = Column(Text)
    ip_address = Column(String(45))

    __table_args__ = (
        Index("idx_audit_time", "time"),
    )
