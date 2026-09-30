import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.models.material import Material
from app.models.scenario import Scenario
from app.models.user import User
from app.services.rule_engine import (
    PRIORITY_WEIGHTS,
    optimize_selection,
    generate_recommendations,
    apply_hard_constraints,
    infer_requirements
)
from app.core.security import create_access_token


def test_priority_weights_exact_mapping():
    """Verify all 4 priority modes map to the exact weights required."""
    assert PRIORITY_WEIGHTS["balanced"]["technical_weight"] == 0.60
    assert PRIORITY_WEIGHTS["balanced"]["cost_weight"] == 0.25
    assert PRIORITY_WEIGHTS["balanced"]["eco_weight"] == 0.15

    assert PRIORITY_WEIGHTS["cost_first"]["technical_weight"] == 0.40
    assert PRIORITY_WEIGHTS["cost_first"]["cost_weight"] == 0.50
    assert PRIORITY_WEIGHTS["cost_first"]["eco_weight"] == 0.10

    assert PRIORITY_WEIGHTS["performance_first"]["technical_weight"] == 0.80
    assert PRIORITY_WEIGHTS["performance_first"]["cost_weight"] == 0.10
    assert PRIORITY_WEIGHTS["performance_first"]["eco_weight"] == 0.10

    assert PRIORITY_WEIGHTS["sustainability_first"]["technical_weight"] == 0.45
    assert PRIORITY_WEIGHTS["sustainability_first"]["cost_weight"] == 0.15
    assert PRIORITY_WEIGHTS["sustainability_first"]["eco_weight"] == 0.40


def test_score_calculation_formula_and_re_ranking():
    """
    Verify final_score = tech_score * tech_w + cost_score * cost_w + eco_score * eco_w
    and test that rankings dynamically change based on priorities.
    """
    # Create 3 candidate materials with different trade-off profiles
    # Mat A: Best Tech (0.95), Higher Cost ($3.00/kg), Moderate Eco (50%)
    mat_a = Material(
        id="mat-a",
        name="High Tech Barrier Laminate",
        mat_type="laminate",
        otr=2.0,
        wvtr=1.0,
        thickness_min=40.0,
        food_contact_safe=True,
        recyclable=False,
        sustainability_score=50.0,
        price_per_kg=350.0,
        material_density_g_cm3=1.35,
        wastage_pct_default=5.0,
        conversion_cost_default=0.40,
        sealing_cost_default=0.10,
        verified=True
    )
    
    # Mat B: Good Tech (0.80), Lowest Cost ($1.20/kg), Moderate Eco (50%)
    mat_b = Material(
        id="mat-b",
        name="Budget Monolayer PP",
        mat_type="PP",
        otr=15.0,
        wvtr=3.0,
        thickness_min=30.0,
        food_contact_safe=True,
        recyclable=True,
        sustainability_score=55.0,
        price_per_kg=120.0,
        material_density_g_cm3=0.90,
        wastage_pct_default=3.0,
        conversion_cost_default=0.20,
        sealing_cost_default=0.08,
        verified=True
    )

    # Mat C: Good Tech (0.78), Moderate Cost ($2.50/kg), Highest Eco (95%)
    mat_c = Material(
        id="mat-c",
        name="Eco Bio-Polymer Film",
        mat_type="biodegradable",
        otr=18.0,
        wvtr=4.0,
        thickness_min=35.0,
        food_contact_safe=True,
        recyclable=False,
        biodegradable=True,
        sustainability_score=95.0,
        price_per_kg=280.0,
        material_density_g_cm3=1.25,
        wastage_pct_default=5.0,
        conversion_cost_default=0.35,
        sealing_cost_default=0.10,
        verified=True
    )

    scenario = Scenario(
        commodity_name="Dry Roasted Almonds",
        commodity_category="dry_goods",
        storage_type="ambient",
        target_shelf_life_days=180,
        product_weight_g=100.0,
        package_format="pouch",
        package_quantity=10000,
        currency="INR"
    )

    candidates_scored = [
        (mat_a, 0.95, ["High Tech Fit"]),
        (mat_b, 0.80, ["Good Tech Fit"]),
        (mat_c, 0.78, ["Good Tech Fit"])
    ]

    with patch("app.services.rule_engine.generate_gemini_explanations", return_value={}):
        # 1. Test Best Performance (80% Tech, 10% Cost, 10% Eco) -> Mat A should win
        res_perf = optimize_selection(candidates_scored, PRIORITY_WEIGHTS["performance_first"], scenario_obj=scenario)
        assert res_perf[0]["material"].id == "mat-a"
        assert res_perf[0]["score_breakdown"]["technical_weight"] == 0.80
        assert res_perf[0]["score_breakdown"]["cost_weight"] == 0.10
        assert res_perf[0]["score_breakdown"]["eco_weight"] == 0.10

        # Verify math formula for top candidate in performance mode
        t_s = res_perf[0]["score_breakdown"]["technical_score"]
        c_s = res_perf[0]["score_breakdown"]["cost_score"]
        e_s = res_perf[0]["score_breakdown"]["eco_score"]
        expected_score = round(t_s * 0.80 + c_s * 0.10 + e_s * 0.10, 4)
        assert res_perf[0]["final_score"] == pytest.approx(expected_score, rel=1e-3)

        # 2. Test Lowest Cost First (40% Tech, 50% Cost, 10% Eco) -> Mat B should win
        res_cost = optimize_selection(candidates_scored, PRIORITY_WEIGHTS["cost_first"], scenario_obj=scenario)
        assert res_cost[0]["material"].id == "mat-b"
        assert res_cost[0]["score_breakdown"]["cost_weight"] == 0.50

        # 3. Test Most Sustainable (45% Tech, 15% Cost, 40% Eco) -> Mat C should win
        res_sust = optimize_selection(candidates_scored, PRIORITY_WEIGHTS["sustainability_first"], scenario_obj=scenario)
        assert res_sust[0]["material"].id == "mat-c"
        assert res_sust[0]["score_breakdown"]["eco_weight"] == 0.40

        # 4. Test Balanced Value (60% Tech, 25% Cost, 15% Eco)
        res_bal = optimize_selection(candidates_scored, PRIORITY_WEIGHTS["balanced"], scenario_obj=scenario)
        assert res_bal[0]["score_breakdown"]["technical_weight"] == 0.60
        assert res_bal[0]["score_breakdown"]["cost_weight"] == 0.25
        assert res_bal[0]["score_breakdown"]["eco_weight"] == 0.15


def test_hard_constraints_strict_even_with_cost_priority():
    """Ensure materials failing food safety or barrier requirements are never recommended, even in cost_first mode."""
    unsafe_mat = Material(
        id="unsafe-1",
        name="Industrial Non-Food Polyethylene",
        food_contact_safe=False,
        price_per_kg=50.0, # extremely cheap
        verified=True
    )
    temp_fail_mat = Material(
        id="temp-fail",
        name="Heat-sensitive LDPE",
        food_contact_safe=True,
        temp_min=0.0,
        temp_max=40.0,
        verified=True
    )
    valid_mat = Material(
        id="valid-mat",
        name="Food Grade Safe HDPE",
        food_contact_safe=True,
        temp_min=-30.0,
        temp_max=100.0,
        price_per_kg=140.0,
        verified=True
    )

    req = infer_requirements(
        commodity_category="frozen_meat",
        moisture_pct=65.0,
        fat_pct=20.0,
        ph=5.8,
        respiration_rate=None,
        storage_type="frozen",
        target_rh=85.0,
        target_shelf_life_days=90
    )

    candidates, excluded = apply_hard_constraints(req, [unsafe_mat, temp_fail_mat, valid_mat])
    candidate_ids = [m.id for m in candidates]
    
    assert "unsafe-1" not in candidate_ids
    assert "temp-fail" not in candidate_ids
    assert "valid-mat" in candidate_ids


def test_missing_scores_fallback_documented():
    """Ensure missing cost/sustainability scores fallback to 0.50 without breaking or zeroing out."""
    mat_no_sus = Material(
        id="mat-no-sus",
        name="Mystery Polymer",
        sustainability_score=None,
        price_per_kg=150.0,
        material_density_g_cm3=1.0,
        verified=True
    )
    scenario = Scenario(
        commodity_name="Snack",
        commodity_category="bakery",
        storage_type="ambient",
        target_shelf_life_days=30
    )

    with patch("app.services.rule_engine.generate_gemini_explanations", return_value={}):
        res = optimize_selection([(mat_no_sus, 0.85, ["Tech fit"])], PRIORITY_WEIGHTS["balanced"], scenario_obj=scenario)
        assert res[0]["eco_score"] == 0.50
        assert res[0]["score_breakdown"]["eco_score"] == 0.50
        assert res[0]["final_score"] > 0.60


from app.core.database import SessionLocal


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


def test_api_scenario_priority_integration(auth_headers):
    """Integration test verifying API PATCH priority and GET recommendations with priority query param."""
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)

    db = SessionLocal()
    admin = db.query(User).filter(User.email == "admin@packsage.ai").first()

    scenario = Scenario(
        user_id=admin.id,
        commodity_name="Premium Roasted Coffee Beans",
        commodity_category="dry_goods",
        storage_type="ambient",
        target_shelf_life_days=365,
        fat_pct=15.0,
        moisture_pct=4.0,
        cost_priority="balanced",
        package_format="pouch",
        product_weight_g=250.0,
        package_quantity=5000,
        currency="INR"
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    scenario_id = scenario.id
    db.close()

    with patch("app.services.rule_engine.generate_gemini_explanations", return_value={}):
        # 1. Test GET recommendations returns applied weights and score breakdown
        res = client.get(f"/api/v1/scenarios/{scenario_id}/recommendations", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["selected_priority"] == "balanced"
        assert data["applied_weights"]["technical_weight"] == 0.60
        assert data["applied_weights"]["cost_weight"] == 0.25
        assert data["applied_weights"]["eco_weight"] == 0.15
        
        top_cand = data["final_ranking"][0]
        assert "score_breakdown" in top_cand
        assert "technical_score" in top_cand["score_breakdown"]
        assert "cost_score" in top_cand["score_breakdown"]
        assert "eco_score" in top_cand["score_breakdown"]
        assert "final_score" in top_cand["score_breakdown"]

        # 2. Test GET recommendations with priority query param override
        res_cost = client.get(f"/api/v1/scenarios/{scenario_id}/recommendations?priority=cost_first", headers=auth_headers)
        assert res_cost.status_code == 200
        data_cost = res_cost.json()
        assert data_cost["selected_priority"] == "cost_first"
        assert data_cost["applied_weights"]["technical_weight"] == 0.40
        assert data_cost["applied_weights"]["cost_weight"] == 0.50
        assert data_cost["applied_weights"]["eco_weight"] == 0.10

        # 3. Test PATCH /priority endpoint
        patch_res = client.patch(
            f"/api/v1/scenarios/{scenario_id}/priority",
            json={"cost_priority": "sustainability_first"},
            headers=auth_headers
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["cost_priority"] == "sustainability_first"
