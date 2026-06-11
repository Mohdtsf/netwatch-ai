import pytest
from unittest.mock import patch, MagicMock

from src.firewall.nftables import NftablesManager
from src.firewall.service import FirewallService
from src.core.models import FirewallRule

@pytest.fixture
def nft_manager():
    return NftablesManager()

@patch("src.firewall.nftables.subprocess.run")
def test_nft_block_ip(mock_run, nft_manager):
    mock_run.return_value = MagicMock(returncode=0)
    result = nft_manager.block_ip("192.168.1.100")
    assert result is True
    mock_run.assert_called_once_with(
        ["nft", "add", "element", "inet", "netwatch", "blocked_ips", "{", "192.168.1.100", "}"],
        capture_output=True,
        text=True,
        check=True
    )

@patch("src.firewall.nftables.subprocess.run")
def test_nft_unblock_mac(mock_run, nft_manager):
    mock_run.return_value = MagicMock(returncode=0)
    result = nft_manager.unblock_mac("00:11:22:33:44:55")
    assert result is True
    mock_run.assert_called_once_with(
        ["nft", "delete", "element", "inet", "netwatch", "blocked_macs", "{", "00:11:22:33:44:55", "}"],
        capture_output=True,
        text=True,
        check=True
    )

@patch("src.firewall.nftables.subprocess.run")
def test_nft_rate_limit(mock_run, nft_manager):
    mock_run.return_value = MagicMock(returncode=0)
    result = nft_manager.set_rate_limit("10.0.0.5")
    assert result is True
    mock_run.assert_called_once_with(
        ["nft", "add", "element", "inet", "netwatch", "rate_limited", "{", "10.0.0.5", "}"],
        capture_output=True,
        text=True,
        check=True
    )

@pytest.mark.asyncio
@patch("src.firewall.service.nft_manager")
async def test_firewall_service_create_rule(mock_nft_manager, db_session):
    # Test FirewallService create rule
    rule = await FirewallService.create_rule(
        db=db_session,
        rule_type="ip",
        target="1.1.1.1",
        action="drop"
    )
    
    assert rule.id is not None
    assert rule.target == "1.1.1.1"
    assert rule.rule_type == "ip"
    
    # Assert nft_manager was called
    mock_nft_manager.block_ip.assert_called_once_with("1.1.1.1")

@pytest.mark.asyncio
@patch("src.firewall.service.nft_manager")
async def test_firewall_service_delete_rule(mock_nft_manager, db_session):
    rule = await FirewallService.create_rule(
        db=db_session,
        rule_type="mac",
        target="aa:bb:cc:dd:ee:ff",
        action="drop"
    )
    
    success = await FirewallService.delete_rule(db_session, rule.id)
    assert success is True
    
    mock_nft_manager.unblock_mac.assert_called_once_with("aa:bb:cc:dd:ee:ff")

@pytest.mark.asyncio
@patch("src.firewall.service.nft_manager")
async def test_sync_all_rules(mock_nft_manager, db_session):
    # Create two rules directly in db to simulate existing
    rule1 = FirewallRule(rule_type="ip", target="2.2.2.2", enabled=True)
    rule2 = FirewallRule(rule_type="mac", target="11:22:33:44:55:66", enabled=True)
    db_session.add(rule1)
    db_session.add(rule2)
    await db_session.commit()
    
    await FirewallService.sync_all_rules(db_session)
    
    mock_nft_manager.block_ip.assert_called_with("2.2.2.2")
    mock_nft_manager.block_mac.assert_called_with("11:22:33:44:55:66")
