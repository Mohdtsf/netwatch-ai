import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.models import DnsRule

pytestmark = pytest.mark.asyncio

async def test_create_dns_rule_admin(async_client: AsyncClient, admin_token_headers: dict, db_session: AsyncSession):
    response = await async_client.post(
        "/api/v1/dns/rules",
        headers=admin_token_headers,
        json={
            "domain_pattern": "malicious.com",
            "action": "block",
            "category": "malware"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain_pattern"] == "malicious.com"
    assert data["action"] == "block"
    assert "id" in data

async def test_create_dns_rule_viewer(async_client: AsyncClient, viewer_token_headers: dict):
    response = await async_client.post(
        "/api/v1/dns/rules",
        headers=viewer_token_headers,
        json={
            "domain_pattern": "malicious.com",
            "action": "block"
        }
    )
    assert response.status_code == 403

async def test_list_dns_rules(async_client: AsyncClient, admin_token_headers: dict):
    # Ensure at least one rule exists
    await async_client.post(
        "/api/v1/dns/rules",
        headers=admin_token_headers,
        json={"domain_pattern": "ads.com", "action": "block"}
    )
    
    response = await async_client.get(
        "/api/v1/dns/rules",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(rule["domain_pattern"] == "ads.com" for rule in data)

async def test_trigger_blocklist_update(async_client: AsyncClient, admin_token_headers: dict):
    response = await async_client.post(
        "/api/v1/dns/blocklist/update",
        headers=admin_token_headers
    )
    assert response.status_code == 202
    assert response.json() == {"message": "Blocklist update triggered"}
