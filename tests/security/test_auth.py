import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_key_auth_missing_key(async_client: AsyncClient):
    # Health should be accessible without key
    resp_health = await async_client.get("/health")
    assert resp_health.status_code == 200

    # Protected route should fail without key
    resp_protected = await async_client.get("/api/v1/datasets/")
    assert resp_protected.status_code == 401

@pytest.mark.asyncio
async def test_api_key_auth_invalid_key(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalid_key"}
    resp = await async_client.get("/api/v1/datasets/", headers=headers)
    assert resp.status_code == 401
