from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.scenario import Scenario, Recommendation, RecommendationItem, Report, AuditLog
from app.models.material import Material
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.services.rule_engine import generate_recommendations as run_hybrid_engine, PRIORITY_WEIGHTS

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# ---- Schemas ----
class ScenarioCreate(BaseModel):
    commodity_name: str
    commodity_category: str
    moisture_pct: Optional[float] = None
    fat_pct: Optional[float] = None
    ph: Optional[float] = None
    respiration_rate: Optional[float] = None
    storage_type: str
    target_rh: Optional[float] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    transport_mode: Optional[str] = None
    transport_days: Optional[float] = None
    target_shelf_life_days: int
    
    # Cost & Production Parameters
    cost_priority: Optional[str] = "balanced" # performance_first | balanced | cost_first | sustainability_first
    package_format: Optional[str] = "pouch"
    product_weight_g: Optional[float] = 100.0
    package_quantity: Optional[int] = 5000
    currency: Optional[str] = "INR"
    target_cost_per_package: Optional[float] = None
    target_total_budget: Optional[float] = None
    package_length_cm: Optional[float] = None
    package_width_cm: Optional[float] = None
    package_height_cm: Optional[float] = None
    film_area_cm2: Optional[float] = None
    custom_thickness_um: Optional[float] = None
    layer_count: Optional[int] = 1
    closure_cost_per_pkg: Optional[float] = None
    label_cost_per_pkg: Optional[float] = None
    printing_cost_per_pkg: Optional[float] = None
    secondary_pack_cost_per_pkg: Optional[float] = None
    labor_packing_cost_per_pkg: Optional[float] = None
    transport_cost_per_pkg: Optional[float] = None
    wastage_pct_override: Optional[float] = None

class ScenarioOut(BaseModel):
    id: str
    commodity_name: str
    commodity_category: str
    storage_type: str
    target_shelf_life_days: int
    cost_priority: Optional[str] = "balanced"
    package_format: Optional[str] = "pouch"
    product_weight_g: Optional[float] = 100.0
    package_quantity: Optional[int] = 5000
    currency: Optional[str] = "INR"
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ScenarioDetail(ScenarioOut):
    moisture_pct: Optional[float]
    fat_pct: Optional[float]
    ph: Optional[float]
    respiration_rate: Optional[float]
    target_rh: Optional[float]
    temp_min: Optional[float]
    temp_max: Optional[float]
    transport_mode: Optional[str]
    transport_days: Optional[float]
    target_cost_per_package: Optional[float]
    target_total_budget: Optional[float]
    package_length_cm: Optional[float]
    package_width_cm: Optional[float]
    package_height_cm: Optional[float]
    film_area_cm2: Optional[float]
    custom_thickness_um: Optional[float]
    layer_count: Optional[int]
    closure_cost_per_pkg: Optional[float]
    label_cost_per_pkg: Optional[float]
    printing_cost_per_pkg: Optional[float]
    secondary_pack_cost_per_pkg: Optional[float]
    labor_packing_cost_per_pkg: Optional[float]
    transport_cost_per_pkg: Optional[float]
    wastage_pct_override: Optional[float]


# ---- Endpoints ----
@router.get("", response_model=List[ScenarioOut])
def list_scenarios(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Scenario).filter(Scenario.user_id == current_user.id)
    if status:
        q = q.filter(Scenario.status == status)
    if search:
        q = q.filter(Scenario.commodity_name.ilike(f"%{search}%"))
    return q.order_by(Scenario.created_at.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=ScenarioDetail, status_code=201)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = Scenario(**payload.dict(), user_id=current_user.id)
    db.add(s)
    db.add(AuditLog(user_id=current_user.id, action="SCENARIO_CREATED", entity_type="scenario", entity_id=s.id))
    db.commit()
    db.refresh(s)
    return s


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    if s.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to access this scenario")
    return s


@router.put("/{scenario_id}", response_model=ScenarioDetail)
def update_scenario(
    scenario_id: str,
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    if s.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to update this scenario")
    for k, v in payload.dict().items():
        setattr(s, k, v)
    s.updated_at = datetime.utcnow()
    db.add(AuditLog(user_id=current_user.id, action="SCENARIO_UPDATED", entity_type="scenario", entity_id=s.id))
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{scenario_id}", status_code=200)
def delete_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    if s.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "You do not have permission to delete this scenario")
    db.delete(s)
    db.add(AuditLog(user_id=current_user.id, action="SCENARIO_DELETED", entity_type="scenario", entity_id=scenario_id))
    db.commit()
    return {"message": "Scenario deleted successfully", "id": scenario_id}


@router.post("/{scenario_id}/generate", status_code=201)
def generate_recommendations_endpoint(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    if s.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to generate recommendations for this scenario")

    materials = db.query(Material).filter(Material.verified == True).all()
    if not materials:
        raise HTTPException(400, "No verified materials in knowledge base. Please ask an admin to verify materials.")

    result_obj = run_hybrid_engine(s, materials)
    result = result_obj.to_dict()

    rec = Recommendation(
        scenario_id=s.id,
        shelf_life_est_min=result["shelf_life"]["min"],
        shelf_life_est_max=result["shelf_life"]["max"],
        dominant_failure_mode=result["shelf_life"]["dominant_failure_mode"],
    )
    db.add(rec)
    db.flush()

    for rank, item in enumerate(result["final_ranking"], start=1):
        mat = item["material"]
        trace_text = item["explanation_text"]
        ri = RecommendationItem(
            recommendation_id=rec.id,
            material_id=mat.id,
            fit_score=item["fit_score"],
            rank=rank,
            explanation_text=trace_text,
        )
        db.add(ri)

    s.status = "completed"
    db.add(AuditLog(
        user_id=current_user.id,
        action="RECOMMENDATION_GENERATED",
        entity_type="recommendation",
        entity_id=rec.id,
    ))
    db.commit()
    db.refresh(rec)

    return {"status": "success", "recommendation_id": rec.id}


class ScenarioPriorityUpdate(BaseModel):
    cost_priority: str = Field(..., description="performance_first | balanced | cost_first | sustainability_first")
    package_quantity: Optional[int] = None
    product_weight_g: Optional[float] = None
    currency: Optional[str] = None
    target_cost_per_package: Optional[float] = None
    target_total_budget: Optional[float] = None


@router.patch("/{scenario_id}/priority", response_model=ScenarioDetail)
def update_scenario_priority(
    scenario_id: str,
    payload: ScenarioPriorityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    if s.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to update this scenario")

    s.cost_priority = payload.cost_priority
    if payload.package_quantity is not None:
        s.package_quantity = payload.package_quantity
    if payload.product_weight_g is not None:
        s.product_weight_g = payload.product_weight_g
    if payload.currency is not None:
        s.currency = payload.currency
    if payload.target_cost_per_package is not None:
        s.target_cost_per_package = payload.target_cost_per_package
    if payload.target_total_budget is not None:
        s.target_total_budget = payload.target_total_budget
        
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return s


@router.get("/{scenario_id}/recommendations")
def get_recommendations(
    scenario_id: str,
    priority: Optional[str] = Query(None, description="Optional priority override: balanced | cost_first | performance_first | sustainability_first"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    if s.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to view recommendations for this scenario")

    if priority:
        s.cost_priority = priority
        s.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(s)

    selected_priority = s.cost_priority or "balanced"
    applied_weights = PRIORITY_WEIGHTS.get(selected_priority, PRIORITY_WEIGHTS["balanced"])

    latest_rec = (
        db.query(Recommendation)
        .filter(Recommendation.scenario_id == s.id)
        .order_by(Recommendation.generated_at.desc())
        .first()
    )
    latest_rec_id = latest_rec.id if latest_rec else None

    materials = db.query(Material).filter(Material.verified == True).all()
    result_obj = run_hybrid_engine(s, materials)
    result = result_obj.to_dict()
    
    # Map the response to the required shape
    final_ranking = []
    for rank, item in enumerate(result["final_ranking"], start=1):
        m = item["material"]
        cb = item.get("cost_breakdown", {})
        score_bd = item.get("score_breakdown", {})

        # Build dynamic pros/cons from material specs
        pros = []
        cons = []
        if m.breathable:
            pros.append("Breathable / MAP compatible for respiration")
        elif (m.otr and m.otr <= 30) or (m.wvtr and m.wvtr <= 10):
            pros.append("High barrier protection against moisture/oxygen")
        if m.recyclable:
            pros.append("100% recyclable polymer stream")
        if m.biodegradable:
            pros.append("Biodegradable / compostable")
        if (m.cost_index or 2.0) <= 2.0:
            pros.append(f"Highly cost efficient (~{cb.get('currency_symbol', '₹')}{cb.get('total_cost_per_pkg', 0):.2f}/pkg)")
        if (m.sustainability_score or 50) >= 70:
            pros.append(f"Superior sustainability index ({m.sustainability_score:.0f}/100)")
        if not pros:
            pros.append("Standard commercial packaging standard")

        if (m.cost_index or 2.0) >= 3.5:
            cons.append(f"Higher procurement cost tier ({cb.get('currency_symbol', '₹')}{cb.get('total_cost_per_pkg', 0):.2f}/pkg)")
        if not m.biodegradable and not m.recyclable:
            cons.append("Limited post-consumer recyclability (multi-layer laminate)")
        if not m.breathable and (s.respiration_rate and s.respiration_rate > 30):
            cons.append("Airtight barrier may cause anaerobic spoilage without micro-perforations")
        if not cons:
            cons.append("Requires standard heat-sealing QA process")

        tech_score = item.get("technical_score", item.get("raw_fit_score", item["fit_score"]))
        cost_score = item.get("cost_score", 0.5)
        eco_score = item.get("eco_score", item.get("sus_score", (m.sustainability_score or 50) / 100.0))
        fin_score = item.get("final_score", item["fit_score"])

        final_ranking.append({
            "rank": rank,
            "material_id": m.id,
            "name": m.name,
            "mat_type": m.mat_type,
            "fit_score": fin_score,
            "final_score": fin_score,
            "raw_fit_score": tech_score,
            "technical_score": tech_score,
            "cost_score": cost_score,
            "sustainability_score": eco_score,
            "eco_score": eco_score,
            "combined_score": fin_score,
            "score_breakdown": score_bd,
            "applied_weights": item.get("applied_weights", applied_weights),
            "otr": m.otr,
            "wvtr": m.wvtr,
            "thickness_microns": cb.get("thickness_microns", getattr(m, "thickness_min", 35) or 35), 
            "food_contact_safe": m.food_contact_safe,
            "recyclable": m.recyclable,
            "biodegradable": m.biodegradable,
            "cost_index": m.cost_index,
            "cost_breakdown": cb,
            "cost_estimate": cb,
            "cost_per_pkg": cb.get("total_cost_per_pkg", 0.0),
            "cost_per_package": cb.get("total_cost_per_pkg", 0.0),
            "cost_per_kg_food": cb.get("cost_per_kg_food", 0.0),
            "total_batch_cost": cb.get("total_batch_cost", 0.0),
            "confidence": cb.get("confidence", "Medium"),
            "explanation": item["explanation_text"] if item.get("explanation_text") else "Scikit-Learn ML evaluated good fit.",
            "trade_offs": {
                "pros": pros,
                "cons": cons
            }
        })
        
    excluded = []
    for exc in result["excluded_with_reasons"]:
        if isinstance(exc, dict):
            excluded.append({
                "material_id": exc.get("material_id", ""),
                "name": exc.get("material_name", ""),
                "reason": exc.get("reason", "")
            })
        else:
            excluded.append({
                "material_id": getattr(exc, "material_id", ""),
                "name": getattr(exc, "material_name", ""),
                "reason": getattr(exc, "reason", "")
            })

    # Four distinct picks (Best Technical, Lowest Cost, Most Sustainable, Balanced Value)
    pareto_picks = {}
    cost_summary = {}
    if final_ranking:
        top_rec = final_ranking[0]
        top_cb = top_rec.get("cost_breakdown", {})
        
        best_tech = max(final_ranking, key=lambda x: x.get("raw_fit_score", 0))
        lowest_cost = min(final_ranking, key=lambda x: x.get("cost_per_pkg", 999999))
        most_sust = max(final_ranking, key=lambda x: x.get("sustainability_score", 0))
        balanced_choice = top_rec

        pareto_picks = {
            "best_technical": {**best_tech, "tag": "Best Technical Performance"},
            "lowest_cost": {**lowest_cost, "tag": "Lowest Packaging Cost"},
            "most_sustainable": {**most_sust, "tag": "Most Sustainable Choice"},
            "balanced_value": {**balanced_choice, "tag": "Best Balanced Value"}
        }

        # Calculate cost share %
        tot_pkg = top_cb.get("total_cost_per_pkg", 1.0)
        mat_pkg = top_cb.get("total_material_cost_per_pkg", 0.0)
        ops_pkg = top_cb.get("total_operations_cost_per_pkg", 0.0)

        cost_summary = {
            "currency": top_cb.get("currency", s.currency or "INR"),
            "currency_symbol": top_cb.get("currency_symbol", "₹"),
            "estimated_cost_per_pkg": top_cb.get("total_cost_per_pkg", 0.0),
            "estimated_cost_per_kg_food": top_cb.get("cost_per_kg_food", 0.0),
            "estimated_cost_per_100g_food": top_cb.get("cost_per_100g_food", 0.0),
            "estimated_total_batch_cost": top_cb.get("total_batch_cost", 0.0),
            "material_cost_share_pct": round((mat_pkg / max(0.001, tot_pkg)) * 100.0, 1),
            "operations_cost_share_pct": round((ops_pkg / max(0.001, tot_pkg)) * 100.0, 1),
            "confidence": top_cb.get("confidence", "Medium"),
            "is_over_budget": top_cb.get("over_budget", False),
            "budget_variance_per_pkg": top_cb.get("budget_variance_per_pkg"),
            "target_cost_per_package": s.target_cost_per_package,
            "target_total_budget": s.target_total_budget,
            "batch_quantity": s.package_quantity or 5000,
            "package_format": s.package_format or "pouch",
            "product_weight_g": s.product_weight_g or 100.0,
            "cost_priority": selected_priority,
            "applied_weights": applied_weights
        }

    return {
        "scenario": {
            "id": s.id,
            "commodity_name": s.commodity_name,
            "commodity_category": s.commodity_category,
            "storage_type": s.storage_type,
            "target_shelf_life_days": s.target_shelf_life_days,
            "moisture_pct": s.moisture_pct,
            "respiration_rate": s.respiration_rate,
            "transport_mode": s.transport_mode,
            "transport_days": s.transport_days,
            "cost_priority": selected_priority,
            "package_format": s.package_format or "pouch",
            "product_weight_g": s.product_weight_g or 100.0,
            "package_quantity": s.package_quantity or 5000,
            "currency": s.currency or "INR",
            "target_cost_per_package": s.target_cost_per_package,
            "target_total_budget": s.target_total_budget,
            "package_length_cm": s.package_length_cm,
            "package_width_cm": s.package_width_cm,
            "package_height_cm": s.package_height_cm,
            "film_area_cm2": s.film_area_cm2
        },
        "selected_priority": selected_priority,
        "priority_mode": selected_priority,
        "applied_weights": applied_weights,
        "requirement_bands": {
            "otr_target": "<= 8000 cc/m2/day (or breathable)" if s.commodity_category == 'fresh_produce' else "<= 25 cc/m2/day",
            "wvtr_target": "5-10 g/m2/day",
            "thickness_target_microns": "30-50",
            "notes": "Fresh produce requires breathable/MAP packaging." if s.commodity_category == 'fresh_produce' else "Barrier protection required."
        },
        "cost_summary": cost_summary,
        "pareto_picks": pareto_picks,
        "recommendation_id": latest_rec_id,
        "ranking_mode": result["ranking_mode"],
        "engine_notes": result["engine_notes"] if result["engine_notes"] else ["Scikit-Learn ML engine ran successfully."],
        "final_ranking": final_ranking,
        "excluded_with_reasons": excluded,
        "shelf_life_estimate": {
            "min_days": result["shelf_life"]["min"],
            "max_days": result["shelf_life"]["max"],
            "confidence": "Scikit-Learn ML calibrated (Random Forest)",
            "dominant_failure_mode": result["shelf_life"]["dominant_failure_mode"]
        },
        "report_available": True
    }


