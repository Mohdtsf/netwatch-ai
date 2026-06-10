"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-06-10

Creates all 10 core tables for NetWatch:
- users, devices, flows, flows_1min, alerts, dns_queries, dns_rules,
  firewall_rules, vpn_peers, audit_log
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════
    # USERS & AUTH
    # ═══════════════════════════════════════════
    op.create_table(
        'users',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('username', sa.String(64), unique=True, nullable=False),
        sa.Column('email', sa.String(256), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(16), server_default='viewer'),
        sa.Column('created_at', sa.Integer()),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # ═══════════════════════════════════════════
    # DEVICES
    # ═══════════════════════════════════════════
    op.create_table(
        'devices',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('mac_address', sa.String(17), unique=True, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('hostname', sa.String(256), nullable=True),
        sa.Column('device_type', sa.String(32), server_default='unknown'),
        sa.Column('custom_name', sa.String(256), nullable=True),
        sa.Column('vendor', sa.String(256), nullable=True),
        sa.Column('os_type', sa.String(64), nullable=True),
        sa.Column('first_seen', sa.Integer()),
        sa.Column('last_seen', sa.Integer()),
        sa.Column('is_blocked', sa.Boolean(), server_default='0'),
        sa.Column('is_online', sa.Boolean(), server_default='0'),
        sa.Column('vpn_enabled', sa.Boolean(), server_default='0'),
        sa.Column('risk_score', sa.Integer(), server_default='0'),
    )
    op.create_index('idx_devices_mac', 'devices', ['mac_address'])
    op.create_index('idx_devices_ip', 'devices', ['ip_address'])
    op.create_index('idx_devices_online', 'devices', ['is_online'])

    # ═══════════════════════════════════════════
    # FLOWS
    # ═══════════════════════════════════════════
    op.create_table(
        'flows',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('time', sa.Integer(), nullable=False),
        sa.Column('src_ip', sa.String(45)),
        sa.Column('dst_ip', sa.String(45)),
        sa.Column('src_port', sa.Integer()),
        sa.Column('dst_port', sa.Integer()),
        sa.Column('protocol', sa.String(10)),
        sa.Column('bytes', sa.Integer(), server_default='0'),
        sa.Column('packets', sa.Integer(), server_default='0'),
        sa.Column('domain', sa.String(256)),
        sa.Column('country', sa.String(3)),
        sa.Column('asn', sa.String(128)),
        sa.Column('anomaly_score', sa.Float(), server_default='0.0'),
        sa.Column('threat_label', sa.String(32), server_default='Normal'),
        sa.Column('device_id', sa.String(32), sa.ForeignKey('devices.id'), nullable=True),
    )
    op.create_index('idx_flows_time', 'flows', ['time'])
    op.create_index('idx_flows_src', 'flows', ['src_ip', 'time'])
    op.create_index('idx_flows_dst', 'flows', ['dst_ip', 'time'])
    op.create_index('idx_flows_device', 'flows', ['device_id', 'time'])

    # ═══════════════════════════════════════════
    # FLOWS 1-MINUTE AGGREGATES
    # ═══════════════════════════════════════════
    op.create_table(
        'flows_1min',
        sa.Column('bucket', sa.Integer(), primary_key=True),
        sa.Column('src_ip', sa.String(45), primary_key=True),
        sa.Column('dst_ip', sa.String(45), primary_key=True),
        sa.Column('total_bytes', sa.Integer(), server_default='0'),
        sa.Column('total_packets', sa.Integer(), server_default='0'),
    )
    op.create_index('idx_flows_1min_bucket', 'flows_1min', ['bucket'])

    # ═══════════════════════════════════════════
    # ALERTS
    # ═══════════════════════════════════════════
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('time', sa.Integer()),
        sa.Column('severity', sa.String(16)),
        sa.Column('type', sa.String(32)),
        sa.Column('message', sa.Text()),
        sa.Column('source_ip', sa.String(45)),
        sa.Column('destination_ip', sa.String(45)),
        sa.Column('device_id', sa.String(32), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('auto_blocked', sa.Boolean(), server_default='0'),
        sa.Column('acknowledged', sa.Boolean(), server_default='0'),
        sa.Column('acknowledged_by', sa.String(32), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('acknowledged_at', sa.Integer(), nullable=True),
    )
    op.create_index('idx_alerts_time', 'alerts', ['time'])
    op.create_index('idx_alerts_severity', 'alerts', ['severity', 'acknowledged'])

    # ═══════════════════════════════════════════
    # DNS QUERIES
    # ═══════════════════════════════════════════
    op.create_table(
        'dns_queries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('time', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(32), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('src_ip', sa.String(45)),
        sa.Column('domain', sa.String(256)),
        sa.Column('query_type', sa.String(10), server_default='A'),
        sa.Column('action', sa.String(16), server_default='allowed'),
        sa.Column('category', sa.String(32)),
    )
    op.create_index('idx_dns_time', 'dns_queries', ['time'])
    op.create_index('idx_dns_device', 'dns_queries', ['device_id', 'time'])
    op.create_index('idx_dns_domain', 'dns_queries', ['domain'])

    # ═══════════════════════════════════════════
    # DNS RULES
    # ═══════════════════════════════════════════
    op.create_table(
        'dns_rules',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('device_id', sa.String(32), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('domain_pattern', sa.String(256), nullable=False),
        sa.Column('action', sa.String(16), server_default='block'),
        sa.Column('category', sa.String(32)),
        sa.Column('created_by', sa.String(32), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.Integer()),
    )

    # ═══════════════════════════════════════════
    # FIREWALL RULES
    # ═══════════════════════════════════════════
    op.create_table(
        'firewall_rules',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('device_id', sa.String(32), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('rule_type', sa.String(16)),
        sa.Column('direction', sa.String(16)),
        sa.Column('target', sa.String(256), nullable=False),
        sa.Column('action', sa.String(16), server_default='drop'),
        sa.Column('schedule', sa.String(64), nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default='1'),
        sa.Column('auto_block', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.Integer()),
        sa.Column('expires_at', sa.Integer(), nullable=True),
    )

    # ═══════════════════════════════════════════
    # VPN PEERS
    # ═══════════════════════════════════════════
    op.create_table(
        'vpn_peers',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('device_id', sa.String(32), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('peer_name', sa.String(128)),
        sa.Column('public_key', sa.String(64), nullable=False),
        sa.Column('private_key_enc', sa.Text(), nullable=True),
        sa.Column('preshared_key_enc', sa.Text(), nullable=True),
        sa.Column('allowed_ips', sa.String(256), server_default='0.0.0.0/0'),
        sa.Column('assigned_ip', sa.String(45)),
        sa.Column('endpoint', sa.String(256), nullable=True),
        sa.Column('tunnel_mode', sa.String(16), server_default='full'),
        sa.Column('enabled', sa.Boolean(), server_default='1'),
        sa.Column('last_handshake', sa.Integer(), nullable=True),
        sa.Column('rx_bytes', sa.Integer(), server_default='0'),
        sa.Column('tx_bytes', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.Integer()),
    )

    # ═══════════════════════════════════════════
    # AUDIT LOG
    # ═══════════════════════════════════════════
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('time', sa.Integer()),
        sa.Column('user_id', sa.String(32), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('target_type', sa.String(32)),
        sa.Column('target_id', sa.String(32)),
        sa.Column('details', sa.Text()),
        sa.Column('ip_address', sa.String(45)),
    )
    op.create_index('idx_audit_time', 'audit_log', ['time'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('vpn_peers')
    op.drop_table('firewall_rules')
    op.drop_table('dns_rules')
    op.drop_table('dns_queries')
    op.drop_table('alerts')
    op.drop_table('flows_1min')
    op.drop_table('flows')
    op.drop_table('devices')
    op.drop_table('users')
