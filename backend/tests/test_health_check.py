import pytest
from httpx import AsyncClient
from backend.main import app
from httpx import AsyncClient
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_health_check():
    # transport = ASGITransport(app=app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "API is running"}
