"""
NetWatch AI — Device Router
REST endpoints for device management.
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_role
from src.devices.schemas import DeviceListResponse, DeviceResponse, DeviceUpdateRequest
from src.devices.service import DeviceService

logger = logging.getLogger("netwatch.devices.router")

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.get(
    "",
    response_model=DeviceListResponse,
    summary="List all discovered devices",
)
async def list_devices(
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """List all devices on the network with online/total counts."""
    service = DeviceService(db)
    result = await service.list_devices()
    return DeviceListResponse(
        devices=[DeviceResponse.model_validate(d) for d in result["devices"]],
        total=result["total"],
        online=result["online"],
    )


@router.get(
    "/scan",
    summary="Trigger ARP network scan",
)
async def trigger_scan(
    current_user=Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an ARP scan to discover devices on the network."""
    service = DeviceService(db)
    return await service.trigger_scan()


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get device details",
)
async def get_device(
    device_id: str,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific device."""
    service = DeviceService(db)
    device = await service.get_device(device_id)
    return DeviceResponse.model_validate(device)


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update device metadata",
)
async def update_device(
    device_id: str,
    data: DeviceUpdateRequest,
    current_user=Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """Update device name or type classification."""
    service = DeviceService(db)
    device = await service.update_device(
        device_id,
        custom_name=data.custom_name,
        device_type=data.device_type,
    )
    return DeviceResponse.model_validate(device)


@router.get(
    "/{device_id}/flows",
    summary="Get device traffic history",
)
async def get_device_flows(
    device_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated traffic flow history for a specific device."""
    service = DeviceService(db)
    flows = await service.get_device_flows(device_id, limit=limit, offset=offset)
    return {"flows": flows, "total": len(flows)}


@router.get(
    "/{device_id}/dns",
    summary="Get device DNS query history",
)
async def get_device_dns(
    device_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated DNS query history for a specific device."""
    service = DeviceService(db)
    dns_queries = await service.get_device_dns(device_id, limit=limit, offset=offset)
    return {"dns_queries": dns_queries, "total": len(dns_queries)}


@router.get(
    "/{device_id}/stats",
    summary="Get device statistics",
)
async def get_device_stats(
    device_id: str,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get calculated statistics for a specific device."""
    service = DeviceService(db)
    return await service.get_device_stats(device_id)


@router.post(
    "/{device_id}/block",
    response_model=DeviceResponse,
    summary="Block a device",
)
async def block_device(
    device_id: str,
    current_user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Block a device from network access. Requires admin role."""
    service = DeviceService(db)
    device = await service.block_device(device_id)
    return DeviceResponse.model_validate(device)


@router.delete(
    "/{device_id}/block",
    response_model=DeviceResponse,
    summary="Unblock a device",
)
async def unblock_device(
    device_id: str,
    current_user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove network block from a device. Requires admin role."""
    service = DeviceService(db)
    device = await service.unblock_device(device_id)
    return DeviceResponse.model_validate(device)
