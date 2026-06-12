import pytest
from unittest.mock import patch, MagicMock

from src.vpn.manager import (
    encrypt_key,
    decrypt_key,
    generate_keys,
    sync_wireguard_config,
    get_wireguard_status
)
from src.vpn.service import generate_client_config, create_peer
from src.core.models import VpnPeer
from src.core.config import settings

def test_encryption():
    # Test encryption/decryption
    original = "a_super_secret_private_key_string"
    encrypted = encrypt_key(original)
    assert encrypted != original
    decrypted = decrypt_key(encrypted)
    assert decrypted == original

@patch("src.vpn.manager.subprocess.run")
def test_generate_keys(mock_run):
    mock_run.side_effect = [
        MagicMock(stdout="priv_key\n", returncode=0),
        MagicMock(stdout="pub_key\n", returncode=0),
        MagicMock(stdout="psk_key\n", returncode=0),
    ]
    
    priv, pub, psk = generate_keys()
    
    assert priv == "priv_key"
    assert pub == "pub_key"
    assert psk == "psk_key"
    assert mock_run.call_count == 3

def test_generate_client_config():
    peer = VpnPeer(
        peer_name="test-peer",
        assigned_ip="10.8.0.2",
        private_key_enc=encrypt_key("priv123"),
        preshared_key_enc=encrypt_key("psk123"),
        tunnel_mode="full",
    )
    
    config = generate_client_config(peer, "server_pub")
    
    assert "PrivateKey = priv123" in config
    assert "PresharedKey = psk123" in config
    assert "PublicKey = server_pub" in config
    assert "AllowedIPs = 0.0.0.0/0" in config
    assert "Address = 10.8.0.2/32" in config

def test_generate_client_config_split():
    peer = VpnPeer(
        peer_name="test-peer-split",
        assigned_ip="10.8.0.3",
        private_key_enc=encrypt_key("priv123"),
        preshared_key_enc=None,
        tunnel_mode="split",
    )
    
    config = generate_client_config(peer, "server_pub")
    
    assert "PrivateKey = priv123" in config
    assert "PresharedKey" not in config
    assert "PublicKey = server_pub" in config
    # Split tunnel allowed IPs should contain local network
    assert settings.SCAN_SUBNET in config
    assert "Address = 10.8.0.3/32" in config

@pytest.mark.asyncio
@patch("src.vpn.service.generate_keys")
@patch("src.vpn.service.apply_server_config")
async def test_create_peer(mock_apply, mock_gen_keys, db_session):
    mock_gen_keys.return_value = ("priv1", "pub1", "psk1")
    
    peer = await create_peer(db_session, "my-laptop", tunnel_mode="full")
    
    assert peer.id is not None
    assert peer.peer_name == "my-laptop"
    assert peer.public_key == "pub1"
    assert peer.assigned_ip == "10.8.0.2"
    assert peer.tunnel_mode == "full"
    
    mock_apply.assert_called_once()
    
    # Decrypt to check
    assert decrypt_key(peer.private_key_enc) == "priv1"
    assert decrypt_key(peer.preshared_key_enc) == "psk1"
