"""
Tests for Shelf-Life-to-Barrier Inverse Solver & Bharat Conditions Simulator
"""
import pytest
from app.services.inverse_solver import solve_inverse_barrier, compute_sustainability_metrics
from app.models.material import Material

def test_inverse_solver_chips_6months_vs_1month():
    # 6 Months (180 days) Potato chips
    res_6m = solve_inverse_barrier(
        commodity_category="oily",
        target_shelf_life_days=180,
        temp_c=32.0,
        rh_pct=60.0,
        pack_weight_grams=100.0,
        pack_area_m2=0.04,
        fat_pct=35.0,
        initial_moisture_pct=2.0,
        critical_moisture_pct=4.5
    )
    wvtr_6m = res_6m["barrier_requirements"]["max_allowable_wvtr"]
    otr_6m = res_6m["barrier_requirements"]["max_allowable_otr"]

    # 1 Month (30 days) Potato chips
    res_1m = solve_inverse_barrier(
        commodity_category="oily",
        target_shelf_life_days=30,
        temp_c=32.0,
        rh_pct=60.0,
        pack_weight_grams=100.0,
        pack_area_m2=0.04,
        fat_pct=35.0,
        initial_moisture_pct=2.0,
        critical_moisture_pct=4.5
    )
    wvtr_1m = res_1m["barrier_requirements"]["max_allowable_wvtr"]
    otr_1m = res_1m["barrier_requirements"]["max_allowable_otr"]

    # 6 months must require much tighter barrier (lower WVTR & lower OTR)
    assert wvtr_6m < wvtr_1m
    assert otr_6m < otr_1m
    assert "Estimated" in res_6m["badges"]["validation_grade"]

def test_bharat_monsoon_humidity_stress():
    # Standard ambient vs Monsoon in Mumbai
    res_std = solve_inverse_barrier(
        commodity_category="dry",
        target_shelf_life_days=90,
        city_name="Indore (Malwa / Central Plateau)",
        season="standard"
    )
    res_monsoon = solve_inverse_barrier(
        commodity_category="dry",
        target_shelf_life_days=90,
        city_name="Mumbai / Coastal Konkan",
        season="monsoon"
    )
    # Monsoon with 90%+ humidity demands stricter WVTR barrier
    assert res_monsoon["barrier_requirements"]["max_allowable_wvtr"] <= res_std["barrier_requirements"]["max_allowable_wvtr"]

def test_fresh_produce_q10_respiration_map():
    res_produce = solve_inverse_barrier(
        commodity_category="fresh_produce",
        target_shelf_life_days=21,
        temp_c=12.0,
        respiration_rate_mg_co2=30.0,
        cold_chain_break_hours=4.0
    )
    assert res_produce["map_produce_details"] is not None
    assert res_produce["map_produce_details"]["cold_chain_breach_detected"] is True
    assert res_produce["map_produce_details"]["recommended_micro_perforations"] > 0

def test_sustainability_waste_saved_ratio():
    fake_mat = Material(
        name="High Barrier Laminate",
        mat_type="laminate",
        thickness_min=40.0,
        cost_index=2.5,
        sustainability_score=75.0
    )
    metrics = compute_sustainability_metrics(
        material_obj=fake_mat,
        target_shelf_life_days=120,
        pack_weight_grams=150.0,
        pack_area_m2=0.04,
        commodity_category="oily"
    )
    assert metrics["packaging_weight_grams"] > 0
    assert metrics["waste_saved_vs_burden_ratio"] > 1.0
    assert "food preserved per gram" in metrics["summary"]
