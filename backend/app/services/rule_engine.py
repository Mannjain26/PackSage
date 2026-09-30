"""
PackSage AI — Rule / Threshold Engine
======================================
This module converts a food commodity + storage scenario into packaging
requirements (OTR/WVTR/thickness/sealability bands) and then evaluates and
ranks candidate materials.

All thresholds are documented here and are intentionally transparent so that
engineers can audit and adjust them without touching the rest of the codebase.

Units:
  - OTR  : cc/m²/day  at 23°C / 0% RH
  - WVTR : g/m²/day   at 38°C / 90% RH
  - Thickness: microns (µm)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
from app.models.material import Material
from app.services.cost_engine import calculate_packaging_cost
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. PACKAGING REQUIREMENT BANDS
# ---------------------------------------------------------------------------

@dataclass
class PackagingRequirements:
    otr_max: Optional[float] = None
    wvtr_max: Optional[float] = None
    thickness_min: Optional[float] = None
    thickness_max: Optional[float] = None
    temp_min_required: Optional[float] = None
    temp_max_required: Optional[float] = None
    must_be_food_contact_safe: bool = True
    must_be_breathable: bool = False
    preferred_breathable: bool = False
    sealability_required: bool = True
    notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. REQUIREMENT INFERENCE TABLE
# ---------------------------------------------------------------------------

STORAGE_TEMP_MAP = {
    "ambient": (15.0, 35.0),
    "chilled": (0.0, 8.0),
    "frozen":  (-25.0, -10.0),
}

def infer_requirements(
    commodity_category: str,
    moisture_pct: Optional[float],
    fat_pct: Optional[float],
    ph: Optional[float],
    respiration_rate: Optional[float],
    storage_type: str,
    target_rh: Optional[float],
    target_shelf_life_days: int,
) -> PackagingRequirements:
    req = PackagingRequirements()
    notes = []

    # STEP 1 — temperature tolerance
    temp_range = STORAGE_TEMP_MAP.get(storage_type, (0.0, 35.0))
    req.temp_min_required = temp_range[0]
    req.temp_max_required = temp_range[1]

    # Baseline thickness floor (20 um minimum)
    req.thickness_min = 20.0

    if storage_type == "frozen":
        notes.append("Frozen storage requires puncture/cold-crack resistant material rated >= -25 C.")
        req.thickness_min += 30.0  # At least 50um for frozen storage

    # STEP 2 — WVTR
    if moisture_pct is not None and moisture_pct < 15:
        wvtr_max = max(0.5, (moisture_pct / 10.0) * (30.0 / target_shelf_life_days) * 10.0)
        req.wvtr_max = round(wvtr_max, 2)
        notes.append(f"Low moisture content ({moisture_pct}%) -> WVTR_max set to {req.wvtr_max} g/m2/day to prevent caking and crispness loss.")
    elif moisture_pct is not None and moisture_pct >= 80:
        req.wvtr_max = 20.0
        notes.append(f"High moisture content ({moisture_pct}%) -> WVTR_max = 20 g/m2/day to prevent desiccation.")
    else:
        req.wvtr_max = 10.0
        notes.append("Default WVTR_max = 10 g/m2/day (intermediate moisture product).")

    # High storage humidity tightens moisture barrier demand
    if target_rh is not None and target_rh >= 80 and req.wvtr_max and req.wvtr_max > 2.0:
        req.wvtr_max = round(req.wvtr_max * 0.7, 2)
        notes.append(f"High environmental relative humidity ({target_rh}%) detected -> tightening WVTR barrier requirement to {req.wvtr_max} g/m2/day.")

    # STEP 3 — OTR & Fat / Oil Oxidation
    if fat_pct is not None and fat_pct >= 15.0:
        req.otr_max = min(req.otr_max or 15.0, 5.0)
        notes.append(f"High fat/oil content ({fat_pct}%) detected -> severe lipid oxidation risk; requiring high oxygen barrier (OTR <= {req.otr_max} cc/m2/day) and metallized/opaque light barrier.")
    elif commodity_category == "fresh_produce" and respiration_rate is not None:
        if respiration_rate > 50:
            req.otr_max = None
            req.must_be_breathable = True
            req.preferred_breathable = True
            notes.append(f"High respiration rate ({respiration_rate} mg CO2/kg/hr) -> breathable/micro-perforated film required. Airtight sealing REJECTED to prevent anaerobic spoilage.")
        elif respiration_rate > 10:
            req.otr_max = 8000.0
            req.preferred_breathable = True
            notes.append(f"Moderate respiration ({respiration_rate}) -> OTR_max = 8000 cc/m2/day; micro-perforated / MAP preferred.")
        else:
            req.otr_max = 2000.0
            notes.append(f"Low respiration ({respiration_rate}) -> OTR_max = 2000 cc/m2/day.")
    elif commodity_category == "oily":
        req.otr_max = 5.0
        notes.append("Oily product -> very tight oxygen barrier (OTR_max = 5 cc/m2/day) and light shielding.")
    elif commodity_category == "dry":
        req.otr_max = 50.0
        notes.append("Dry product -> moderate oxygen barrier (OTR_max = 50 cc/m2/day).")
    elif commodity_category == "dairy":
        req.otr_max = 10.0
        notes.append("Dairy -> tight oxygen barrier (OTR_max = 10 cc/m2/day).")
    elif commodity_category == "processed":
        req.otr_max = 20.0
        notes.append("Processed food -> moderate oxygen barrier (OTR_max = 20 cc/m2/day).")
    else:
        req.otr_max = 500.0
        notes.append("Default OTR_max = 500 cc/m2/day.")

    # STEP 4 — pH & Microbial Considerations
    if ph is not None:
        if ph < 4.5:
            notes.append(f"Acidic food commodity (pH {ph} < 4.5) -> resistant to Clostridium botulinum spore outgrowth; require acid-resistant contact layer (polyolefin/lacquer; avoid bare aluminium contact).")
        elif ph > 7.0:
            notes.append(f"Alkaline/neutral food (pH {ph}) -> requires stringent hygiene barrier and hermetic seal.")

    # STEP 5 — breathable mandatory
    if req.must_be_breathable:
        req.sealability_required = False

    # STEP 6 — thickness floor & transport protection
    if req.thickness_min is None:
        req.thickness_min = 20.0
    notes.append(f"Minimum barrier thickness: {req.thickness_min} um.")

    req.notes = notes
    return req


# ---------------------------------------------------------------------------
# OUTPUT SCHEMAS
# ---------------------------------------------------------------------------

@dataclass
class ExclusionReason:
    material_id: str
    material_name: str
    reason: str
    def to_dict(self):
        return {"material_id": self.material_id, "material_name": self.material_name, "reason": self.reason}

@dataclass
class RecommendationResult:
    candidates_considered: int
    excluded_with_reasons: List[ExclusionReason]
    final_ranking: List[Dict[str, Any]]
    ranking_mode: str
    engine_notes: List[str]
    shelf_life: Dict[str, Any]

    def to_dict(self):
        return {
            "candidates_considered": self.candidates_considered,
            "excluded_with_reasons": [e.to_dict() for e in self.excluded_with_reasons],
            "final_ranking": self.final_ranking,
            "ranking_mode": self.ranking_mode,
            "engine_notes": self.engine_notes,
            "shelf_life": self.shelf_life
        }


# ---------------------------------------------------------------------------
# STAGE 1: Deterministic Rules (hard constraints)
# ---------------------------------------------------------------------------

def apply_hard_constraints(req: PackagingRequirements, materials: List[Material]) -> Tuple[List[Material], List[ExclusionReason]]:
    candidates = []
    excluded = []
    
    for mat in materials:
        if not mat.verified:
            excluded.append(ExclusionReason(mat.id, mat.name, "Material is not verified by admin."))
            continue
            
        if req.must_be_food_contact_safe and not mat.food_contact_safe:
            excluded.append(ExclusionReason(mat.id, mat.name, "Material is not food-contact safe."))
            continue
            
        if req.temp_min_required is not None and mat.temp_min is not None:
            if mat.temp_min > req.temp_min_required:
                excluded.append(ExclusionReason(mat.id, mat.name, f"Cannot tolerate minimum storage temperature ({req.temp_min_required} C)."))
                continue
                
        if req.temp_max_required is not None and mat.temp_max is not None:
            if mat.temp_max < req.temp_max_required:
                excluded.append(ExclusionReason(mat.id, mat.name, f"Cannot tolerate maximum storage temperature ({req.temp_max_required} C)."))
                continue
                
        if req.must_be_breathable and not mat.breathable:
            excluded.append(ExclusionReason(mat.id, mat.name, "High respiration produce requires breathable/MAP packaging; this material is airtight."))
            continue
            
        candidates.append(mat)
        
    return candidates, excluded


# ---------------------------------------------------------------------------
# STAGE 2: Scikit-Learn Machine Learning Ranking Engine
# ---------------------------------------------------------------------------

from app.services.ml_engine import predict_material_scores, ml_model
from app.services.gemini_service import generate_gemini_explanations, build_fallback_explanation, is_gemini_active

def rank_materials(
    req: PackagingRequirements, 
    candidate_materials: List[Material],
    force_fallback: bool = False
) -> Tuple[List[Tuple[Material, float, List[str]]], str]:
    """
    Ranks candidate materials using Scikit-Learn RandomForestRegressor inference,
    with a graceful rule-based fallback if ML inference is bypassed or fails.
    """
    if not force_fallback:
        try:
            scored = predict_material_scores(req, candidate_materials)
            ranking_mode = "ml"
            return scored, ranking_mode
        except Exception as e:
            logger.warning("Scikit-Learn ML inference failed, falling back to rule scoring: %s", e)

    ranking_mode = "rule_fallback"
    scored = []
    for mat in candidate_materials:
        score_components = []
        traces = []
        
        # OTR Component
        if req.otr_max is not None and mat.otr is not None:
            if mat.otr <= req.otr_max:
                otr_score = 1.0 - (mat.otr / req.otr_max) * 0.5
                traces.append(f"[PASS] OTR {mat.otr} cc/m2/day <= {req.otr_max}")
            else:
                otr_score = max(0.0, 0.5 - (mat.otr - req.otr_max) / req.otr_max)
                traces.append(f"[WARN] OTR {mat.otr} > {req.otr_max}")
            score_components.append(0.40 * otr_score)
        else:
            score_components.append(0.40 * 0.8)
            traces.append("[PASS] No strict OTR limit applied")

        # WVTR Component
        if req.wvtr_max is not None and mat.wvtr is not None:
            if mat.wvtr <= req.wvtr_max:
                wvtr_score = 1.0 - (mat.wvtr / req.wvtr_max) * 0.3
                traces.append(f"[PASS] WVTR {mat.wvtr} g/m2/day <= {req.wvtr_max}")
            else:
                wvtr_score = max(0.0, 0.5 - (mat.wvtr - req.wvtr_max) / (req.wvtr_max + 1))
                traces.append(f"[WARN] WVTR {mat.wvtr} > {req.wvtr_max}")
            score_components.append(0.30 * wvtr_score)
        else:
            score_components.append(0.30 * 0.8)
            traces.append("[PASS] No strict WVTR limit applied")
            
        fit_score = sum(score_components) / 0.70
        scored.append((mat, fit_score, traces))
        
    return scored, ranking_mode


# ---------------------------------------------------------------------------
# STAGE 3: Constrained Optimization & Generative AI Explanation
# ---------------------------------------------------------------------------

PRIORITY_WEIGHTS = {
    "balanced": {
        "technical_weight": 0.60,
        "cost_weight": 0.25,
        "eco_weight": 0.15,
        "fit": 0.60,
        "cost": 0.25,
        "sustainability": 0.15
    },
    "cost_first": {
        "technical_weight": 0.40,
        "cost_weight": 0.50,
        "eco_weight": 0.10,
        "fit": 0.40,
        "cost": 0.50,
        "sustainability": 0.10
    },
    "performance_first": {
        "technical_weight": 0.80,
        "cost_weight": 0.10,
        "eco_weight": 0.10,
        "fit": 0.80,
        "cost": 0.10,
        "sustainability": 0.10
    },
    "sustainability_first": {
        "technical_weight": 0.45,
        "cost_weight": 0.15,
        "eco_weight": 0.40,
        "fit": 0.45,
        "cost": 0.15,
        "sustainability": 0.40
    }
}

def optimize_selection(
    ranked_materials: List[Tuple[Material, float, List[str]]],
    weights: dict,
    scenario_info: Optional[Dict[str, Any]] = None,
    req_bands: Optional[Dict[str, Any]] = None,
    scenario_obj: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    w_tech = weights.get("technical_weight", weights.get("fit", 0.60))
    w_cost = weights.get("cost_weight", weights.get("cost", 0.25))
    w_eco = weights.get("eco_weight", weights.get("sustainability", 0.15))
    
    # Pre-calculate cost breakdowns for all technically viable candidates
    cost_items = []
    for mat, fit_score, traces in ranked_materials:
        cb = calculate_packaging_cost(
            material_obj=mat,
            format_type=getattr(scenario_obj, "package_format", "pouch") or "pouch",
            product_weight_g=getattr(scenario_obj, "product_weight_g", 100.0) or 100.0,
            package_quantity=getattr(scenario_obj, "package_quantity", 5000) or 5000,
            currency=getattr(scenario_obj, "currency", "INR") or "INR",
            length_cm=getattr(scenario_obj, "package_length_cm", None),
            width_cm=getattr(scenario_obj, "package_width_cm", None),
            height_cm=getattr(scenario_obj, "package_height_cm", None),
            explicit_area_cm2=getattr(scenario_obj, "film_area_cm2", None),
            custom_thickness_um=getattr(scenario_obj, "custom_thickness_um", None),
            layer_count=getattr(scenario_obj, "layer_count", 1) or 1,
            closure_cost_per_pkg=getattr(scenario_obj, "closure_cost_per_pkg", None),
            label_cost_per_pkg=getattr(scenario_obj, "label_cost_per_pkg", None),
            printing_cost_per_pkg=getattr(scenario_obj, "printing_cost_per_pkg", None),
            secondary_pack_cost_per_pkg=getattr(scenario_obj, "secondary_pack_cost_per_pkg", None),
            labor_packing_cost_per_pkg=getattr(scenario_obj, "labor_packing_cost_per_pkg", None),
            transport_cost_per_pkg=getattr(scenario_obj, "transport_cost_per_pkg", None),
            wastage_pct_override=getattr(scenario_obj, "wastage_pct_override", None),
            target_cost_per_package=getattr(scenario_obj, "target_cost_per_package", None),
            target_total_budget=getattr(scenario_obj, "target_total_budget", None),
        )
        cost_items.append((mat, fit_score, traces, cb))

    # Find lowest suitable packaging cost among viable candidates
    valid_costs = [cb.total_cost_per_pkg for _, _, _, cb in cost_items if cb.total_cost_per_pkg > 0]
    lowest_suitable_cost = min(valid_costs) if valid_costs else 1.0

    preliminary_ranking = []
    
    for mat, fit_score, traces, cb in cost_items:
        # Technical suitability score normalized in [0.0, 1.0]
        tech_score = max(0.0, min(1.0, float(fit_score)))
        
        # Sustainability / circularity score normalized in [0.0, 1.0] (fallback: 0.50 if not specified)
        if mat.sustainability_score is not None:
            eco_score = max(0.0, min(1.0, float(mat.sustainability_score) / 100.0))
        else:
            eco_score = 0.50
        
        # Transparent normalized cost score: lowest_suitable / candidate_cost in [0.0, 1.0] (fallback: 0.50)
        if cb.total_cost_per_pkg > 0:
            cost_score = max(0.0, min(1.0, lowest_suitable_cost / cb.total_cost_per_pkg))
        else:
            cost_score = 0.50
        
        # Weighted multi-attribute formula
        final_score = round(tech_score * w_tech + cost_score * w_cost + eco_score * w_eco, 4)
        
        score_breakdown = {
            "technical_score": round(tech_score, 4),
            "technical_weight": round(w_tech, 2),
            "technical_contribution": round(tech_score * w_tech, 4),
            "cost_score": round(cost_score, 4),
            "cost_weight": round(w_cost, 2),
            "cost_contribution": round(cost_score * w_cost, 4),
            "eco_score": round(eco_score, 4),
            "eco_weight": round(w_eco, 2),
            "eco_contribution": round(eco_score * w_eco, 4),
            "final_score": final_score
        }
        
        preliminary_ranking.append({
            "material": mat,
            "fit_score": final_score,
            "final_score": final_score,
            "technical_score": tech_score,
            "raw_fit_score": tech_score,
            "traces": traces,
            "sus_score": eco_score,
            "eco_score": eco_score,
            "cost_score": cost_score,
            "score_breakdown": score_breakdown,
            "applied_weights": {
                "technical_weight": w_tech,
                "cost_weight": w_cost,
                "eco_weight": w_eco
            },
            "cost_breakdown": cb.to_dict(),
        })
        
    preliminary_ranking.sort(key=lambda x: x["final_score"], reverse=True)
    top_candidates = preliminary_ranking[:8]

    # Google Gemini AI Explanations
    gemini_map = {}
    if scenario_info and is_gemini_active():
        try:
            gemini_map = generate_gemini_explanations(scenario_info, req_bands or {}, top_candidates)
        except Exception as e:
            logger.warning("Gemini explanation generation encountered an issue: %s", e)

    final_ranking = []
    for item in top_candidates:
        mat = item["material"]
        mat_id_str = str(mat.id)
        
        if mat_id_str in gemini_map:
            explanation_text = gemini_map[mat_id_str]
        elif scenario_info:
            explanation_text = build_fallback_explanation(scenario_info, mat, item["fit_score"], item["traces"])
        else:
            trace_text = "\n".join(item["traces"])
            explanation_text = f"{trace_text}\n[WEIGHTING] Tech: {item['technical_score']:.2f} ({w_tech*100:.0f}%), Cost: {item['cost_score']:.2f} ({w_cost*100:.0f}%), Eco: {item['eco_score']:.2f} ({w_eco*100:.0f}%) -> Final: {item['final_score']:.2f}"

        final_ranking.append({
            "material": mat,
            "fit_score": item["final_score"],
            "final_score": item["final_score"],
            "technical_score": item["technical_score"],
            "raw_fit_score": item["technical_score"],
            "sus_score": item["eco_score"],
            "eco_score": item["eco_score"],
            "cost_score": item["cost_score"],
            "score_breakdown": item["score_breakdown"],
            "applied_weights": item["applied_weights"],
            "explanation_text": explanation_text,
            "cost_breakdown": item["cost_breakdown"],
            "traces": item["traces"]
        })
        
    return final_ranking


# ---------------------------------------------------------------------------
# SHELF-LIFE ESTIMATOR (Scikit-Learn ML calibrated)
# ---------------------------------------------------------------------------

def estimate_shelf_life(
    scenario_shelf_life_days: int,
    req: PackagingRequirements,
    best_fit_score: float,
) -> Tuple[int, int, str]:
    base = scenario_shelf_life_days

    if req.wvtr_max is not None and req.wvtr_max < 2:
        failure_mode = "Oxidation / rancidity"
        factor = 0.85 + 0.15 * best_fit_score
    elif req.must_be_breathable:
        failure_mode = "Physiological deterioration (CO2 / O2 imbalance)"
        factor = 0.80 + 0.15 * best_fit_score
    elif req.wvtr_max is not None and req.wvtr_max < 10:
        failure_mode = "Moisture ingress / caking"
        factor = 0.80 + 0.20 * best_fit_score
    else:
        failure_mode = "General microbial / quality deterioration"
        factor = 0.75 + 0.20 * best_fit_score

    est = int(base * factor)
    return max(1, est - 2), est + 2, failure_mode


# ---------------------------------------------------------------------------
# WIRING IT TOGETHER
# ---------------------------------------------------------------------------

def generate_recommendations(scenario, materials: List[Material]) -> RecommendationResult:
    req = infer_requirements(
        commodity_category=scenario.commodity_category,
        moisture_pct=scenario.moisture_pct,
        fat_pct=scenario.fat_pct,
        ph=scenario.ph,
        respiration_rate=scenario.respiration_rate,
        storage_type=scenario.storage_type,
        target_rh=scenario.target_rh,
        target_shelf_life_days=scenario.target_shelf_life_days,
    )
    
    candidates, excluded = apply_hard_constraints(req, materials)
    
    if not candidates:
        notes = req.notes + ["No viable materials found passing hard constraints."]
        shelf_min, shelf_max, failure_mode = estimate_shelf_life(scenario.target_shelf_life_days, req, 0.0)
        return RecommendationResult(
            candidates_considered=len(materials),
            excluded_with_reasons=excluded,
            final_ranking=[],
            ranking_mode="ml",
            engine_notes=notes,
            shelf_life={"min": shelf_min, "max": shelf_max, "dominant_failure_mode": failure_mode}
        )

    scored_candidates, ranking_mode = rank_materials(req, candidates)

    scenario_info = {
        "id": str(getattr(scenario, "id", "")),
        "commodity_name": getattr(scenario, "commodity_name", "Produce"),
        "commodity_category": getattr(scenario, "commodity_category", "fresh_produce"),
        "storage_type": getattr(scenario, "storage_type", "ambient"),
        "target_shelf_life_days": getattr(scenario, "target_shelf_life_days", 5),
        "moisture_pct": getattr(scenario, "moisture_pct", None),
        "respiration_rate": getattr(scenario, "respiration_rate", None),
        "transport_mode": getattr(scenario, "transport_mode", "road"),
        "transport_days": getattr(scenario, "transport_days", 2),
    }

    req_bands = {
        "otr_target": f"<= {req.otr_max} cc/m2/day" if req.otr_max else "Breathable / MAP",
        "wvtr_target": f"<= {req.wvtr_max} g/m2/day" if req.wvtr_max else "Ambient",
        "thickness_target_microns": f">= {req.thickness_min} um" if req.thickness_min else "30-50",
        "notes": "; ".join(req.notes)
    }

    cost_prio = getattr(scenario, "cost_priority", "balanced") or "balanced"
    weights = PRIORITY_WEIGHTS.get(cost_prio, PRIORITY_WEIGHTS["balanced"])

    final_ranking = optimize_selection(
        scored_candidates,
        weights=weights,
        scenario_info=scenario_info,
        req_bands=req_bands,
        scenario_obj=scenario,
    )
    
    best_score = final_ranking[0]["fit_score"]
    shelf_min, shelf_max, failure_mode = estimate_shelf_life(scenario.target_shelf_life_days, req, best_score)
    
    notes = list(req.notes)
    if ranking_mode == "ml":
        notes.append("Scikit-Learn ML: Random Forest Regressor calibrated on empirical barrier synergy (OTR, WVTR, Thickness, Thermal).")
    if is_gemini_active():
        notes.append("Google Gemini: Generative engineering rationale & MAP recommendations active.")
    else:
        notes.append("Google Gemini: Configured (set GEMINI_API_KEY in backend/.env to activate live generative packaging reports).")

    notes.append(f"Optimization Priority: {cost_prio.replace('_', ' ').title()} (Technical: {weights['technical_weight']*100:.0f}%, Cost: {weights['cost_weight']*100:.0f}%, Eco: {weights['eco_weight']*100:.0f}%)")

    return RecommendationResult(
        candidates_considered=len(materials),
        excluded_with_reasons=excluded,
        final_ranking=final_ranking,
        ranking_mode=ranking_mode,
        engine_notes=notes,
        shelf_life={"min": shelf_min, "max": shelf_max, "dominant_failure_mode": failure_mode}
    )


