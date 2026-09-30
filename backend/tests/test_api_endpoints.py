from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
import pytest

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PackSage AI"

def test_ready_endpoint():
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}

def test_auth_login_invalid():
    res = client.post("/api/v1/auth/login", data={"username": "fake@test.com", "password": "wrongpassword"})
    assert res.status_code == 400

def test_auth_login_demo_admin():
    res = client.post("/api/v1/auth/login", data={"username": "admin@packsage.ai", "password": "Admin@123"})
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["role"] == "admin"

    # Verify /me endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@packsage.ai"
