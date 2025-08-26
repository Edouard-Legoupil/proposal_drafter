import pytest
from httpx import AsyncClient
from backend.main import app
from httpx import AsyncClient
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "لْحَمْدُ لِلَّٰهِ -- API is running"
