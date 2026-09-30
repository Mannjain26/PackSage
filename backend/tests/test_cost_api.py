import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.material import Material
from app.models.scenario import Scenario
from app.core.security import create_access_token
from app.services import gemini_service

client = TestClient(fastapi_app)


@pytest.fixture
def auth_headers():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "admin@packsage.ai").first()
    if not user:
        user = User(
            name="Admin User",
            email="admin@packsage.ai",
            role="admin",
            password_hash=User.hash_password("Admin@123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = str(user.id)
    db.close()
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def test_get_cost_formats():
    response = client.get("/api/v1/cost/formats")
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    assert "pouch" in data["formats"]
    assert "tray_lidding" in data["formats"]


def test_cost_estimate_endpoint(auth_headers):
    payload = {
        "price_per_kg": 180.0,
        "currency": "INR",
        "material_density_g_cm3": 0.92,
        "film_area_cm2": 600.0,
        "custom_thickness_um": 40.0,
        "package_format": "pouch",
        "package_quantity": 20000,
        "product_weight_g": 100.0
    }
    response = client.post("/api/v1/cost/estimate", json=payload, headers=auth_headers)
    assert response.status_code == 200
    res = response.json()
    assert "cost_breakdown" in res
    assert res["cost_breakdown"]["total_cost_per_pkg"] > 0
    assert res["cost_breakdown"]["total_batch_cost"] > 0
    assert res["cost_breakdown"]["currency"] == "INR"


@patch("app.services.rule_engine.generate_gemini_explanations", return_value={})
def test_scenario_creation_with_cost_and_recommendation(mock_gemini, auth_headers):
    # Create scenario for Potato Chips (oily) with cost priority
    payload = {
        "commodity_name": "Test Crunchy Chips",
        "commodity_category": "oily",
        "moisture_pct": 2.0,
        "fat_pct": 32.0,
        "ph": 6.2,
        "storage_type": "ambient",
        "target_rh": 50.0,
        "target_shelf_life_days": 120,
        "cost_priority": "cost_first",
        "package_format": "pouch",
        "product_weight_g": 100.0,
        "package_quantity": 25000,
        "currency": "INR",
        "target_cost_per_package": 2.50
    }
    res = client.post("/api/v1/scenarios", json=payload, headers=auth_headers)
    assert res.status_code == 201
    scenario_id = res.json()["id"]

    # Generate recommendations
    rec_res = client.post(f"/api/v1/scenarios/{scenario_id}/generate", headers=auth_headers)
    assert rec_res.status_code in [200, 201]
    
    # Fetch full recommendation details
    get_res = client.get(f"/api/v1/scenarios/{scenario_id}/recommendations", headers=auth_headers)
    assert get_res.status_code == 200
    rec_data = get_res.json()

    assert "final_ranking" in rec_data
    assert len(rec_data["final_ranking"]) > 0
    assert "cost_estimate" in rec_data["final_ranking"][0]
    assert "pareto_picks" in rec_data
    assert "lowest_cost" in rec_data["pareto_picks"]
    assert "best_technical" in rec_data["pareto_picks"]

    # Test changing priority to performance_first
    prio_res = client.patch(
        f"/api/v1/scenarios/{scenario_id}/priority",
        json={"cost_priority": "performance_first"},
        headers=auth_headers
    )
    assert prio_res.status_code == 200
    assert prio_res.json()["cost_priority"] == "performance_first"

