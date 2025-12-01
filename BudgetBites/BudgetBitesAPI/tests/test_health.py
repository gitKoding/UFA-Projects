import pytest
import httpx
from httpx import ASGITransport
from src.server.app import app


@pytest.mark.asyncio
async def test_health_ok():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert "service" in data