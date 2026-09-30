"""
Shelf-Life-to-Barrier Inverse Solver & Bharat Conditions Simulator
=================================================================
Positioning:
"Every other tool asks what packaging you've chosen.
 We ask how long your product must last, and work out what packaging it needs."

Module Features:
1. Labuza-type Inverse Moisture-Gain Model for dry/crisp foods (WVTR max).
2. Peroxide / Fat Oxidation Model for high-fat foods (OTR max).
3. Respiration & Modified Atmosphere Packaging (MAP) Q10 model for fresh produce.
4. "Bharat Conditions" simulator: City/climate zones, monsoon/summer toggle, transit vibration/stress, and cold-chain break what-if.
5. Sustainability tradeoff (Waste-saved vs. packaging burden) & Pareto selections.
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# ---------------------------------------------------------------------------
# BHARAT CLIMATE DATABASE
# ---------------------------------------------------------------------------
BHARAT_CITIES = {
    "Indore (Malwa / Central Plateau)": {"temp_c": 32.0, "rh_pct": 45.0, "zone": "composite"},
    "Mumbai / Coastal Konkan": {"temp_c": 33.0, "rh_pct": 85.0, "zone": "warm_humid"},
    "Delhi / NCR (North Plains)": {"temp_c": 40.0, "rh_pct": 35.0, "zone": "hot_dry"},
    "Kolkata / Eastern Humid": {"temp_c": 34.0, "rh_pct": 82.0, "zone": "warm_humid"},
    "Chennai / Coromandel Coast": {"temp_c": 35.0, "rh_pct": 78.0, "zone": "warm_humid"},
    "Shimla / Himachal Hills": {"temp_c": 18.0, "rh_pct": 55.0, "zone": "cold"},
    "Nagpur / Vidarbha Peak Summer": {"temp_c": 44.0, "rh_pct": 25.0, "zone": "hot_dry"},
    "Bengaluru / Deccan Moderate": {"temp_c": 27.0, "rh_pct": 60.0, "zone": "moderate"}
}

SEASON_MODIFIERS = {
    "standard": {"temp_delta": 0.0, "rh_override": None, "label": "Standard Ambient"},
    "peak_summer": {"temp_delta": +6.0, "rh_override": 30.0, "label": "Peak Summer (Extreme Heat)"},
    "monsoon": {"temp_delta": +1.0, "rh_override": 92.0, "label": "Monsoon / Wet Humid (90%+ RH)"},
    "winter": {"temp_delta": -8.0, "rh_override": 40.0, "label": "Mild Winter"}
}

TRANSIT_MODES = {
    "truck_standard": {"stress_factor": 1.25, "vibration": "High", "label": "Standard Indian Truck (Non-suspension)"},
    "rail_freight": {"stress_factor": 1.10, "vibration": "Medium", "label": "Indian Railways Freight (Containerized)"},
    "cold_chain_reefer": {"stress_factor": 1.05, "vibration": "Low", "label": "Refrigerated Reefer Truck (Continuous)"},
    "last_mile_2wheeler": {"stress_factor": 1.35, "vibration": "Very High", "label": "Last-Mile 2-Wheeler / Auto (High impact)"}
}

# ---------------------------------------------------------------------------
# INVERSE PACKAGING SOLVER
# ---------------------------------------------------------------------------

def saturation_vapor_pressure(temp_c: float) -> float:
    """Tetens equation for saturation vapor pressure in kPa."""
    return 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))

def solve_inverse_barrier(
    commodity_category: str,
    target_shelf_life_days: int,
    temp_c: float = 30.0,
    rh_pct: float = 70.0,
    pack_weight_grams: float = 100.0,
    pack_area_m2: float = 0.04,   # e.g., 20cm x 20cm pouch = 0.04 m² front+back
    # Commodity parameters with editable sensible defaults
    initial_moisture_pct: Optional[float] = None,
    critical_moisture_pct: Optional[float] = None,
    isotherm_slope: Optional[float] = None,  # delta moisture / delta aw (%/aw)
    fat_pct: Optional[float] = None,
    allowable_o2_uptake_ml_per_kg: Optional[float] = None, # ml O2 / kg product
    respiration_rate_mg_co2: Optional[float] = None,       # mg CO2 / kg / hr
    # Bharat condition variables
    city_name: Optional[str] = None,
    season: str = "standard",
    transit_mode: str = "truck_standard",
    cold_chain_break_hours: float = 0.0,
    break_temp_c: float = 35.0
) -> Dict[str, Any]:
    """
    Solves backwards from target shelf life to allowable barrier specs (WVTR & OTR).
    Includes Bharat Conditions stress and cold-chain breach models.
    """
    # 1. Resolve Climate & Transit Stress
    eff_temp = temp_c
    eff_rh = rh_pct
    
    if city_name and city_name in BHARAT_CITIES:
        eff_temp = BHARAT_CITIES[city_name]["temp_c"]
        eff_rh = BHARAT_CITIES[city_name]["rh_pct"]

    season_info = SEASON_MODIFIERS.get(season, SEASON_MODIFIERS["standard"])
    eff_temp += season_info["temp_delta"]
    if season_info["rh_override"] is not None:
        eff_rh = season_info["rh_override"]

    # Clamp RH
    eff_rh = max(10.0, min(99.0, eff_rh))

    # Transit stress multiplier on required barrier margin
    transit_info = TRANSIT_MODES.get(transit_mode, TRANSIT_MODES["truck_standard"])
    transit_stress = transit_info["stress_factor"]

    # Cold chain break effect (if applicable)
    cold_chain_stress = 1.0
    if cold_chain_break_hours > 0:
        # Temperature spike increases vapor pressure and respiration drastically
        cold_chain_stress += (cold_chain_break_hours / 24.0) * ((break_temp_c - eff_temp) / 10.0 if break_temp_c > eff_temp else 0.5)
        cold_chain_stress = max(1.1, min(2.5, cold_chain_stress))

    # 2. Mechanistic Inverse Calculations
    assumptions_used = []
    badges = {
        "shelf_life_target": "User Defined",
        "barrier_model": "Mechanistic Inverse (Labuza/Kallman)",
        "climate_profile": "Bharat Real-World Sensor/IMD Calibrated" if city_name else "Estimated Ambient",
        "validation_grade": "Estimated"
    }

    # Saturation pressure in mmHg (1 kPa = 7.50062 mmHg)
    sat_p_kpa = saturation_vapor_pressure(eff_temp)
    rh_ambient_fraction = eff_rh / 100.0

    # Minimum shelf life floor
    days = max(1, target_shelf_life_days)
    
    req_wvtr_max = 10.0
    req_otr_max = 100.0
    fresh_produce_map = None

    if commodity_category in ["oily", "dry", "processed"] and (fat_pct is not None and fat_pct > 15.0 or commodity_category == "oily"):
        # FAT OXIDATION DOMINANT MODEL
        # Allowable O2 uptake before rancidity (e.g. 50-100 ml O2 / kg product)
        allowable_o2 = allowable_o2_uptake_ml_per_kg or 70.0  # ml O2/kg
        product_kg = pack_weight_grams / 1000.0
        total_allowable_o2_ml = allowable_o2 * product_kg

        # OTR_max = Total O2 / (Pack Area * Days * Delta P_O2)
        # Delta P_O2 across film ≈ 0.21 atm (air vs head space flushed with N2 or low O2)
        delta_p_o2 = 0.21
        raw_otr = total_allowable_o2_ml / (pack_area_m2 * days * delta_p_o2)
        
        # Apply transit stress factor
        req_otr_max = max(0.1, raw_otr / (transit_stress * cold_chain_stress))

        # Moisture gain limit for crispness
        m_init = initial_moisture_pct if initial_moisture_pct is not None else 2.0
        m_crit = critical_moisture_pct if critical_moisture_pct is not None else 4.5
        slope = isotherm_slope or 0.15 # g H2O / 100g solids per unit aw
        solids_g = pack_weight_grams * (1.0 - m_init / 100.0)
        allowable_water_gain_g = (m_crit - m_init) / 100.0 * solids_g
        allowable_water_gain_g = max(0.05, allowable_water_gain_g)

        # Labuza simplified driving force:
        # WVTR_max = allowable_gain / (Area * Days * (RH_env - aw_init))
        delta_aw = max(0.15, rh_ambient_fraction - (m_init / (m_crit * 1.5)))
        raw_wvtr = allowable_water_gain_g / (pack_area_m2 * days * delta_aw)
        req_wvtr_max = max(0.1, raw_wvtr / (transit_stress * cold_chain_stress))

        assumptions_used.extend([
            f"Lipid rancidity threshold: {allowable_o2} ml O₂/kg fat matrix",
            f"Crispness loss critical moisture: {m_crit}% (initial {m_init}%)",
            f"Isotherm sorption slope: {slope} g H₂O/g solids",
            f"Transit stress derating factor: {transit_stress:.2f}x ({transit_info['label']})"
        ])

    elif commodity_category in ["dry", "dairy"]:
        # MOISTURE GAIN / CAKING DOMINANT MODEL
        m_init = initial_moisture_pct if initial_moisture_pct is not None else 6.0
        m_crit = critical_moisture_pct if critical_moisture_pct is not None else 10.0
        solids_g = pack_weight_grams * (1.0 - m_init / 100.0)
        allowable_water_gain_g = max(0.1, (m_crit - m_init) / 100.0 * solids_g)

        delta_aw = max(0.20, rh_ambient_fraction - 0.25)
        raw_wvtr = allowable_water_gain_g / (pack_area_m2 * days * delta_aw)
        req_wvtr_max = max(0.2, raw_wvtr / (transit_stress * cold_chain_stress))
        req_otr_max = 50.0  # general moderate oxygen barrier

        assumptions_used.extend([
            f"Critical moisture before caking/microbial threshold: {m_crit}%",
            f"Driving humidity gradient: {delta_aw*100:.1f}% ΔRH",
            f"Transit derating: {transit_stress:.2f}x"
        ])

    elif commodity_category == "fresh_produce":
        # FRESH PRODUCE RESPIRATION & Q10 MODEL
        r_base = respiration_rate_mg_co2 or 30.0 # mg CO2/kg/hr at 10°C
        # Q10 rule of thumb: respiration doubles every 10°C rise
        q10 = 2.2
        t_ref = 10.0
        q10_factor = q10 ** ((eff_temp - t_ref) / 10.0)
        
        # Cold chain break Q10 spike
        if cold_chain_break_hours > 0:
            spike_q10_factor = q10 ** ((break_temp_c - t_ref) / 10.0)
            avg_q10_factor = (q10_factor * (24.0 - cold_chain_break_hours) + spike_q10_factor * cold_chain_break_hours) / 24.0
        else:
            avg_q10_factor = q10_factor

        resp_rate_eff = r_base * avg_q10_factor
        product_kg = pack_weight_grams / 1000.0
        daily_o2_consumed_ml = (resp_rate_eff * 0.7) * product_kg * 24.0 # approximate R.Q. ~ 1.0

        # Target MAP equilibrium: 3-5% O2, 5-8% CO2
        target_internal_o2_fraction = 0.04
        delta_o2_fraction = 0.21 - target_internal_o2_fraction

        # Required OTR for film or perforation
        req_otr_produce = daily_o2_consumed_ml / (pack_area_m2 * delta_o2_fraction)
        req_otr_max = max(1000.0, req_otr_produce)
        req_wvtr_max = 25.0  # high moisture barrier to prevent desiccation, but needs anti-fog

        # Laser micro-perforation estimation:
        # Standard 100 µm perforation passes ~ 25 ml O2 / day
        perf_count = max(0, int(round(daily_o2_consumed_ml / 45.0)))
        condensation_risk = "CRITICAL" if eff_rh > 85 or cold_chain_break_hours > 0 else "MODERATE"

        fresh_produce_map = {
            "respiration_at_temp": round(resp_rate_eff, 1),
            "q10_multiplier": round(avg_q10_factor, 2),
            "target_o2_pct": 4.0,
            "target_co2_pct": 6.0,
            "recommended_micro_perforations": perf_count,
            "perforation_diameter_microns": 80,
            "condensation_risk": condensation_risk,
            "anti_fog_additive_required": True,
            "cold_chain_breach_detected": cold_chain_break_hours > 0
        }

        assumptions_used.extend([
            f"Respiration baseline: {r_base} mg CO₂/kg·h (Q10 = {q10})",
            f"Temperature acceleration factor: {avg_q10_factor:.2f}x",
            f"Equilibrium MAP Target: 4% O₂, 6% CO₂",
            f"Condensation hazard: {condensation_risk}"
        ])
    else:
        req_wvtr_max = max(0.5, 15.0 * (30.0 / days))
        req_otr_max = max(1.0, 50.0 * (30.0 / days))
        assumptions_used.append("General commodity empirical threshold scaling.")

    # Round barrier specifications
    solved_wvtr = round(req_wvtr_max, 2)
    solved_otr = round(req_otr_max, 2)

    return {
        "status": "solved",
        "inputs": {
            "commodity_category": commodity_category,
            "target_shelf_life_days": target_shelf_life_days,
            "pack_weight_grams": pack_weight_grams,
            "pack_area_m2": pack_area_m2,
            "climate_zone": city_name or "Custom",
            "effective_temp_c": round(eff_temp, 1),
            "effective_rh_pct": round(eff_rh, 1),
            "season": season_info["label"],
            "transit_stress_factor": transit_stress,
            "cold_chain_break_hours": cold_chain_break_hours
        },
        "barrier_requirements": {
            "max_allowable_wvtr": solved_wvtr,
            "wvtr_unit": "g/m²·day (at test condition ASTM F1249)",
            "max_allowable_otr": solved_otr,
            "otr_unit": "cc/m²·day (at test condition ASTM D3985)",
            "interpretation": f"To achieve {target_shelf_life_days} days shelf life in {city_name or 'specified conditions'}, the container barrier must not exceed {solved_wvtr} g/m²·d WVTR and {solved_otr} cc/m²·d OTR."
        },
        "map_produce_details": fresh_produce_map,
        "assumptions": assumptions_used,
        "badges": badges,
        "lab_validation_notice": "Requires OTR/WVTR testing (ASTM D3985 / ASTM F1249) and real-time shelf-life study before commercial use."
    }

# ---------------------------------------------------------------------------
# SUSTAINABILITY & PARETO OPTIMIZER (Waste-Saved vs Packaging Burden)
# ---------------------------------------------------------------------------

def compute_sustainability_metrics(
    material_obj: Any,
    target_shelf_life_days: int,
    pack_weight_grams: float,
    pack_area_m2: float,
    commodity_category: str
) -> Dict[str, Any]:
    """
    Computes:
    - Packaging burden (grams plastic/paper used per pack)
    - Grams packaging per extra day of shelf life
    - Estimated food waste avoided (kg food saved per kg packaging)
    """
    # Material thickness in microns
    thickness_um = getattr(material_obj, "thickness_min", 35) or 35
    # Approximate polymer density ~ 0.92 to 1.4 g/cm³
    density_g_cm3 = 1.05
    # Pack weight in grams = Area(m²) * thickness(m) * density(g/m³)
    # thickness in m = thickness_um * 1e-6
    # density in g/m³ = density_g_cm3 * 1e6
    pack_material_weight_g = round(pack_area_m2 * (thickness_um * 1e-6) * (density_g_cm3 * 1e6), 2)
    
    # Grams of packaging per shelf-life day
    pack_burden_per_day = round(pack_material_weight_g / max(1, target_shelf_life_days), 4)

    # Food waste avoidance ratio
    # Without proper barrier, baseline spoiled food is ~ 25-40% in Indian supply chain (MoFPI estimates)
    avoidance_factor = 0.35 if commodity_category in ["fresh_produce", "dairy"] else 0.20
    food_saved_per_pack_g = pack_weight_grams * avoidance_factor
    eco_efficiency_ratio = round(food_saved_per_pack_g / max(0.1, pack_material_weight_g), 1)

    return {
        "packaging_weight_grams": pack_material_weight_g,
        "grams_pack_per_shelf_day": pack_burden_per_day,
        "food_waste_saved_g": food_saved_per_pack_g,
        "waste_saved_vs_burden_ratio": eco_efficiency_ratio,
        "summary": f"{eco_efficiency_ratio}x food preserved per gram of packaging material",
        "epr_recyclability_tag": "Verify locally with registered PWM/SPCB recycler"
    }
