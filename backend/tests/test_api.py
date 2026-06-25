import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com", "full_name": "Test User", "password": "Test@1234"
        })
        assert reg.status_code in (201, 400)
        login = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com", "password": "Test@1234"
        })
        if reg.status_code == 201:
            assert login.status_code == 200
            assert "access_token" in login.json()
