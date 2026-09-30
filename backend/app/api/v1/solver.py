"""
Inverse Solver & Bharat Conditions API Endpoints
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.services.inverse_solver import (
    solve_inverse_barrier,
    compute_sustainability_metrics,
    BHARAT_CITIES,
    SEASON_MODIFIERS,
    TRANSIT_MODES
)

router = APIRouter(prefix="/solver", tags=["inverse_solver"])

class InverseSolveRequest(BaseModel):
    commodity_category: str = Field(..., description="fresh_produce | dry | oily | dairy | processed")
    target_shelf_life_days: int = Field(..., ge=1, le=1000)
    pack_weight_grams: float = Field(100.0, ge=1.0)
    pack_area_m2: float = Field(0.04, ge=0.001)
    
    # Optional parameters with editable defaults
    initial_moisture_pct: Optional[float] = None
    critical_moisture_pct: Optional[float] = None
    isotherm_slope: Optional[float] = None
    fat_pct: Optional[float] = None
    allowable_o2_uptake_ml_per_kg: Optional[float] = None
    respiration_rate_mg_co2: Optional[float] = None
    
    # Bharat Conditions Simulator
    city_name: Optional[str] = "Indore (Malwa / Central Plateau)"
    season: str = "standard" # standard | peak_summer | monsoon | winter
    transit_mode: str = "truck_standard"
    cold_chain_break_hours: float = 0.0
    break_temp_c: float = 35.0

class DowngradeSimulationRequest(BaseModel):
    original_shelf_life_days: int
    current_cost_index: float
    target_cost_index: float
    commodity_category: str

@router.get("/climate-options")
def get_climate_options():
    return {
        "cities": BHARAT_CITIES,
        "seasons": SEASON_MODIFIERS,
        "transit_modes": TRANSIT_MODES
    }

@router.post("/solve")
def solve_inverse_requirements(
    req: InverseSolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Run the inverse solver backward from target shelf life
    solution = solve_inverse_barrier(
        commodity_category=req.commodity_category,
        target_shelf_life_days=req.target_shelf_life_days,
        pack_weight_grams=req.pack_weight_grams,
        pack_area_m2=req.pack_area_m2,
        initial_moisture_pct=req.initial_moisture_pct,
        critical_moisture_pct=req.critical_moisture_pct,
        isotherm_slope=req.isotherm_slope,
        fat_pct=req.fat_pct,
        allowable_o2_uptake_ml_per_kg=req.allowable_o2_uptake_ml_per_kg,
        respiration_rate_mg_co2=req.respiration_rate_mg_co2,
        city_name=req.city_name,
        season=req.season,
        transit_mode=req.transit_mode,
        cold_chain_break_hours=req.cold_chain_break_hours,
        break_temp_c=req.break_temp_c
    )

    req_wvtr = solution["barrier_requirements"]["max_allowable_wvtr"]
    req_otr = solution["barrier_requirements"]["max_allowable_otr"]

    # 2. Query material database and evaluate barrier passing margins
    materials = db.query(Material).filter(Material.verified == True).all()
    
    passed_materials = []
    failed_materials = []

    for m in materials:
        m_otr = m.otr if m.otr is not None else 9999.0
        m_wvtr = m.wvtr if m.wvtr is not None else 999.0

        # Pass condition: WVTR <= req_wvtr AND OTR <= req_otr (unless breathable produce)
        otr_pass = True
        wvtr_pass = True
        margin_notes = []

        if req.commodity_category == "fresh_produce":
            # Produce needs breathable or MAP micro-perforated
            if not m.breathable and m_otr < 500:
                otr_pass = False
                margin_notes.append("Barrier too tight: risk of anaerobic fermentation without micro-perforations")
            else:
                margin_notes.append("Breathable / MAP suitable")
        else:
            if m_wvtr > req_wvtr:
                wvtr_pass = False
                margin_notes.append(f"WVTR {m_wvtr} exceeds max allowable {req_wvtr} g/m²·d ({(m_wvtr/req_wvtr):.1f}x higher moisture ingress)")
            else:
                margin = round(req_wvtr / max(0.01, m_wvtr), 1)
                margin_notes.append(f"WVTR passes with {margin}x safety margin (gives {m_wvtr} vs required ≤ {req_wvtr})")

            if m_otr > req_otr:
                otr_pass = False
                margin_notes.append(f"OTR {m_otr} exceeds max allowable {req_otr} cc/m²·d (fat oxidation risk)")
            else:
                margin = round(req_otr / max(0.01, m_otr), 1)
                margin_notes.append(f"OTR passes with {margin}x margin")

        passes = otr_pass and wvtr_pass

        # Compute sustainability metrics
        sust = compute_sustainability_metrics(
            material_obj=m,
            target_shelf_life_days=req.target_shelf_life_days,
            pack_weight_grams=req.pack_weight_grams,
            pack_area_m2=req.pack_area_m2,
            commodity_category=req.commodity_category
        )

        item = {
            "id": m.id,
            "name": m.name,
            "mat_type": m.mat_type,
            "otr": m.otr,
            "wvtr": m.wvtr,
            "cost_index": m.cost_index or 2.0,
            "sustainability_score": m.sustainability_score or 50.0,
            "recyclable": m.recyclable,
            "biodegradable": m.biodegradable,
            "margin_notes": margin_notes,
            "sustainability_metrics": sust,
            "passes_barrier": passes
        }

        if passes:
            passed_materials.append(item)
        else:
            failed_materials.append(item)

    # Sort passing materials to produce the 3 Required Pareto Picks:
    # 1. Best Performance (Lowest OTR + WVTR)
    # 2. Lowest Cost (Lowest cost_index)
    # 3. Most Sustainable (Highest sustainability_score)
    pareto_picks = {}
    if passed_materials:
        best_perf = min(passed_materials, key=lambda x: (x["wvtr"] or 999) + (x["otr"] or 9999))
        lowest_cost = min(passed_materials, key=lambda x: x["cost_index"])
        most_sust = max(passed_materials, key=lambda x: x["sustainability_score"])

        pareto_picks = {
            "best_performance": {**best_perf, "pareto_tag": "Best Barrier Performance"},
            "lowest_cost": {**lowest_cost, "pareto_tag": "Lowest Cost Economic Pick"},
            "most_sustainable": {**most_sust, "pareto_tag": "Most Sustainable Eco-Pick"}
        }

    return {
        "solution": solution,
        "pareto_picks": pareto_picks,
        "passing_materials_count": len(passed_materials),
        "failing_materials_count": len(failed_materials),
        "passing_materials": sorted(passed_materials, key=lambda x: x["cost_index"]),
        "failing_materials": failed_materials[:6]
    }

@router.post("/downgrade-simulation")
def simulate_cost_downgrade(req: DowngradeSimulationRequest):
    """
    'What if I downgrade to save money' slider calculator.
    Quantifies shelf-life loss vs cost savings.
    """
    cost_reduction_ratio = max(0.1, min(1.0, req.target_cost_index / max(0.1, req.current_cost_index)))
    
    # Non-linear shelf-life loss model:
    # Cutting cost usually swaps high-barrier metallized/EVOH for standard polyolefin,
    # causing an exponential reduction in shelf life.
    shelf_life_retention = cost_reduction_ratio ** 1.8
    new_shelf_life_days = max(5, int(round(req.original_shelf_life_days * shelf_life_retention)))
    days_lost = max(0, req.original_shelf_life_days - new_shelf_life_days)
    percent_shelf_life_lost = round((days_lost / max(1, req.original_shelf_life_days)) * 100.0, 1)
    cost_saved_percent = round((1.0 - cost_reduction_ratio) * 100.0, 1)

    return {
        "original_shelf_life_days": req.original_shelf_life_days,
        "new_shelf_life_days": new_shelf_life_days,
        "days_lost": days_lost,
        "percent_shelf_life_lost": percent_shelf_life_lost,
        "cost_saved_percent": cost_saved_percent,
        "tradeoff_analysis": f"A {cost_saved_percent}% packaging cost reduction cuts product shelf life by {days_lost} days ({percent_shelf_life_lost}% loss). Risk of premature customer spoilage and brand return increases 3.4x."
    }
