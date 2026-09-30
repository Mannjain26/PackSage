"""
Packaging Cost Estimation, Comparison, and Optimization Engine
=============================================================
Calculates exact material mass, raw material cost, cutting/sealing scrap wastage,
conversion, printing, labeling, closure, and transport costs across single/multi-layer
packaging formats with full unit safety.

Units:
- Package Dimensions: cm
- Film Area: cm² and m²
- Thickness: microns (µm) and cm
- Material Density: g/cm³ (and kg/m³)
- Material Mass: grams (g) and kilograms (kg)
- Product Weight: grams (g) and kilograms (kg)
- Currency: explicit ISO code (INR, USD, EUR)
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Standard Currencies & Reference Conversion Rates (Base = INR)
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€"
}

CURRENCY_RATES_TO_INR = {
    "INR": 1.0,
    "USD": 84.0,
    "EUR": 92.0
}

# Standard Packaging Format Geometries (if explicit length/width not given)
FORMAT_DEFAULTS = {
    "pouch": {
        "label": "Flexible Pouch (Stand-up / 3-Side Seal)",
        "wastage_pct": 5.0,
        "conversion_cost_inr": 0.25,
        "sealing_cost_inr": 0.10,
    },
    "bag": {
        "label": "Gusseted Bag / Pillow Bag",
        "wastage_pct": 4.0,
        "conversion_cost_inr": 0.20,
        "sealing_cost_inr": 0.08,
    },
    "sachet": {
        "label": "Unit Sachet / Stick Pack",
        "wastage_pct": 6.0,
        "conversion_cost_inr": 0.15,
        "sealing_cost_inr": 0.05,
    },
    "tray_lidding": {
        "label": "Thermoformed Tray + Lidding Film",
        "wastage_pct": 8.0,
        "conversion_cost_inr": 0.85,
        "sealing_cost_inr": 0.20,
    },
    "bottle": {
        "label": "Rigid Bottle / Container",
        "wastage_pct": 3.0,
        "conversion_cost_inr": 1.50,
        "sealing_cost_inr": 0.25,
    },
    "jar": {
        "label": "Rigid Wide-Mouth Jar",
        "wastage_pct": 3.5,
        "conversion_cost_inr": 1.80,
        "sealing_cost_inr": 0.30,
    },
    "box": {
        "label": "Folding Carton / Liner Box",
        "wastage_pct": 5.0,
        "conversion_cost_inr": 1.20,
        "sealing_cost_inr": 0.15,
    },
    "bulk": {
        "label": "Bulk Liner / Sack / Crate",
        "wastage_pct": 2.5,
        "conversion_cost_inr": 2.50,
        "sealing_cost_inr": 0.40,
    },
    "custom": {
        "label": "Custom Package Configuration",
        "wastage_pct": 5.0,
        "conversion_cost_inr": 0.30,
        "sealing_cost_inr": 0.10,
    }
}

FORMAT_DEFAULT_SPECS = FORMAT_DEFAULTS

# Material Densities in g/cm³ (if not in Material DB)
DEFAULT_DENSITIES = {
    "LDPE": 0.92,
    "HDPE": 0.95,
    "PP": 0.90,
    "BOPP": 0.91,
    "PET": 1.38,
    "metalized": 1.35,
    "foil_laminate": 1.85,
    "high_barrier": 1.20,
    "biodegradable": 1.25,
    "breathable": 0.92,
    "nylon": 1.15,
    "paper": 0.80,
    "shrink": 1.25,
    "vsp": 1.05
}

def convert_currency(amount: float, from_curr: str, to_curr: str) -> float:
    """Converts amounts between supported currencies via base INR rate."""
    if from_curr == to_curr or amount == 0.0:
        return amount
    from_rate = CURRENCY_RATES_TO_INR.get(from_curr.upper(), 1.0)
    to_rate = CURRENCY_RATES_TO_INR.get(to_curr.upper(), 1.0)
    in_inr = amount * from_rate
    return in_inr / to_rate

def estimate_film_area_cm2(
    format_type: str,
    product_weight_g: float,
    length_cm: Optional[float] = None,
    width_cm: Optional[float] = None,
    height_cm: Optional[float] = None,
    explicit_area_cm2: Optional[float] = None
) -> Tuple[float, str]:
    """
    Computes total package surface/film area in cm².
    Returns (area_cm2, calculation_method_explanation).
    """
    if explicit_area_cm2 and explicit_area_cm2 > 0:
        return explicit_area_cm2, f"User-specified exact film area ({explicit_area_cm2:.1f} cm²)"

    # If geometric dimensions are supplied
    if length_cm and width_cm and length_cm > 0 and width_cm > 0:
        l = length_cm
        w = width_cm
        h = height_cm or 0.0
        
        if format_type in ["pouch", "sachet"]:
            # 2 sides (front + back) + sealing margins (1.5 cm around perimeter)
            area = 2 * (l * w)
            return area, f"Calculated 2-ply flat pouch area: 2 × ({l} cm × {w} cm) = {area:.1f} cm²"
        elif format_type == "bag":
            # Gusseted bag: 2*(L*W + L*H + W*H)
            area = 2 * (l * w + l * h + w * h) if h > 0 else 2.2 * (l * w)
            return area, f"Calculated gusseted bag envelope: {area:.1f} cm²"
        elif format_type == "tray_lidding":
            # Tray container surface + lid film
            tray_area = (l * w) + 2 * (l * h + w * h)
            lid_area = (l * w) * 1.15 # 15% flange overhang
            area = tray_area + lid_area
            return area, f"Calculated tray body + lidding film: {area:.1f} cm²"
        else:
            area = 2 * (l * w + l * h + w * h) if h > 0 else 2 * (l * w)
            return area, f"Calculated standard 3D envelope: {area:.1f} cm²"

    # Sensible empirical estimation based on food product fill weight (grams)
    # Assumes average food bulk density ~ 0.5 - 0.9 g/cm³
    w_g = max(5.0, product_weight_g)
    
    if format_type == "sachet":
        # e.g., 5-25g spice/sauce sachet -> ~ 60 - 140 cm²
        area = max(40.0, 2.0 * math.sqrt(w_g * 15.0) * 8.0)
        return area, f"Empirical sachet scaling for {w_g:.0f}g fill weight: {area:.1f} cm²"
    elif format_type == "pouch":
        # e.g., 100g chips pouch (approx 20cm x 15cm = 300cm² per side x 2 = 600cm² front+back)
        # 50g -> ~380 cm², 100g -> ~550 cm², 500g -> ~1200 cm²
        estimated_side_area = 55.0 + 4.8 * math.pow(w_g, 0.78)
        area = 2.0 * estimated_side_area
        return area, f"Standard pouch geometry model for {w_g:.0f}g fill: {area:.1f} cm² (2 × {estimated_side_area:.1f} cm²)"
    elif format_type == "tray_lidding":
        area = 150.0 + 3.5 * w_g
        return area, f"Thermoformed tray + lid model for {w_g:.0f}g fill: {area:.1f} cm²"
    elif format_type in ["bottle", "jar"]:
        area = 100.0 + 2.2 * w_g
        return area, f"Rigid container surface scaling for {w_g:.0f}g fill: {area:.1f} cm²"
    else:
        # Default flexible container envelope
        area = 80.0 + 4.5 * math.pow(w_g, 0.8)
        return area, f"Empirical food package envelope for {w_g:.0f}g fill: {area:.1f} cm²"


def calculate_film_area_cm2(
    format_type: str = "pouch",
    product_weight_g: float = 100.0,
    length_cm: Optional[float] = None,
    width_cm: Optional[float] = None,
    height_cm: Optional[float] = None,
    explicit_area_cm2: Optional[float] = None
) -> float:
    area, _ = estimate_film_area_cm2(format_type, product_weight_g, length_cm, width_cm, height_cm, explicit_area_cm2)
    return area


@dataclass
class CostBreakdown:
    # Per Package Metrics
    film_area_cm2: float
    film_area_m2: float
    thickness_microns: float
    density_g_cm3: float
    material_mass_grams: float
    material_mass_kg: float
    
    # Cost items (in requested currency)
    currency: str
    currency_symbol: str
    material_cost_per_pkg: float
    wastage_pct: float
    wastage_cost_per_pkg: float
    conversion_cost_per_pkg: float
    sealing_cost_per_pkg: float
    printing_cost_per_pkg: float
    label_cost_per_pkg: float
    closure_cost_per_pkg: float
    secondary_pack_cost_per_pkg: float
    labor_packing_cost_per_pkg: float
    transport_cost_per_pkg: float
    
    # Aggregates
    total_material_cost_per_pkg: float   # Material + Scrap
    total_operations_cost_per_pkg: float # Forming + Seal + Print + Label + Closure + Freight + Labor
    total_cost_per_pkg: float
    
    # Food Unit Metrics
    product_weight_grams: float
    cost_per_kg_food: float
    cost_per_100g_food: float
    
    # Production Batch Metrics
    batch_quantity: int
    total_batch_material_mass_kg: float
    gross_batch_cost_before_discount: float
    quantity_discount_pct: float
    quantity_discount_amount: float
    total_batch_cost: float
    
    # Commercial MOQ Checks
    moq_kg: float
    moq_met: bool
    moq_purchase_cost_required: Optional[float]
    
    # Budget Variance
    target_cost_per_package: Optional[float]
    budget_variance_per_pkg: Optional[float]
    over_budget: bool
    
    # Meta & Traceability
    price_per_kg_used: float
    price_source: str
    price_last_updated: str
    confidence: str # High | Medium | Low | Illustrative Demo
    assumptions: List[str] = field(default_factory=list)
    included_components: List[str] = field(default_factory=list)
    excluded_components: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        material_share = round((self.total_material_cost_per_pkg / max(0.0001, self.total_cost_per_pkg)) * 100, 1)
        ops_share = round((self.total_operations_cost_per_pkg / max(0.0001, self.total_cost_per_pkg)) * 100, 1)

        breakdown_dict = {
            "material_mass_g": round(self.material_mass_grams, 3),
            "material_mass_kg": round(self.material_mass_kg, 6),
            "raw_material_cost": round(self.material_cost_per_pkg, 4),
            "wastage_pct": round(self.wastage_pct, 1),
            "scrap_wastage_cost": round(self.wastage_cost_per_pkg, 4),
            "converting_cost": round(self.conversion_cost_per_pkg, 4),
            "sealing_cost": round(self.sealing_cost_per_pkg, 4),
            "printing_cost": round(self.printing_cost_per_pkg, 4),
            "label_cost": round(self.label_cost_per_pkg, 4),
            "closure_cost": round(self.closure_cost_per_pkg, 4),
            "secondary_pack_cost": round(self.secondary_pack_cost_per_pkg, 4),
            "labor_packing_cost": round(self.labor_packing_cost_per_pkg, 4),
            "transport_cost": round(self.transport_cost_per_pkg, 4),
            "total_material_cost": round(self.total_material_cost_per_pkg, 4),
            "total_operations_cost": round(self.total_operations_cost_per_pkg, 4),
            "total_cost_per_pkg": round(self.total_cost_per_pkg, 4),
            "cost_per_package": round(self.total_cost_per_pkg, 4),
        }

        return {
            "film_area_cm2": round(self.film_area_cm2, 2),
            "film_area_m2": round(self.film_area_m2, 4),
            "thickness_microns": round(self.thickness_microns, 1),
            "density_g_cm3": round(self.density_g_cm3, 3),
            "material_density_g_cm3": round(self.density_g_cm3, 3),
            "material_mass_grams": round(self.material_mass_grams, 3),
            "material_mass_g": round(self.material_mass_grams, 3),
            "material_mass_kg": round(self.material_mass_kg, 6),
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "material_cost_per_pkg": round(self.material_cost_per_pkg, 4),
            "raw_material_cost": round(self.material_cost_per_pkg, 4),
            "wastage_pct": round(self.wastage_pct, 1),
            "wastage_cost_per_pkg": round(self.wastage_cost_per_pkg, 4),
            "scrap_wastage_cost": round(self.wastage_cost_per_pkg, 4),
            "conversion_cost_per_pkg": round(self.conversion_cost_per_pkg, 4),
            "converting_cost": round(self.conversion_cost_per_pkg, 4),
            "sealing_cost_per_pkg": round(self.sealing_cost_per_pkg, 4),
            "sealing_cost": round(self.sealing_cost_per_pkg, 4),
            "printing_cost_per_pkg": round(self.printing_cost_per_pkg, 4),
            "label_cost_per_pkg": round(self.label_cost_per_pkg, 4),
            "closure_cost_per_pkg": round(self.closure_cost_per_pkg, 4),
            "secondary_pack_cost_per_pkg": round(self.secondary_pack_cost_per_pkg, 4),
            "labor_packing_cost_per_pkg": round(self.labor_packing_cost_per_pkg, 4),
            "transport_cost_per_pkg": round(self.transport_cost_per_pkg, 4),
            "total_material_cost_per_pkg": round(self.total_material_cost_per_pkg, 4),
            "total_operations_cost_per_pkg": round(self.total_operations_cost_per_pkg, 4),
            "total_cost_per_pkg": round(self.total_cost_per_pkg, 4),
            "cost_per_package": round(self.total_cost_per_pkg, 4),
            "cost_per_pkg": round(self.total_cost_per_pkg, 4),
            "material_cost_share_pct": material_share,
            "operations_cost_share_pct": ops_share,
            "product_weight_grams": round(self.product_weight_grams, 1),
            "product_weight_g": round(self.product_weight_grams, 1),
            "cost_per_kg_food": round(self.cost_per_kg_food, 2),
            "cost_per_100g_food": round(self.cost_per_100g_food, 3),
            "batch_quantity": self.batch_quantity,
            "package_quantity": self.batch_quantity,
            "total_batch_material_mass_kg": round(self.total_batch_material_mass_kg, 2),
            "gross_batch_cost_before_discount": round(self.gross_batch_cost_before_discount, 2),
            "quantity_discount_pct": round(self.quantity_discount_pct, 1),
            "quantity_discount_amount": round(self.quantity_discount_amount, 2),
            "total_batch_cost": round(self.total_batch_cost, 2),
            "moq_kg": self.moq_kg,
            "moq_met": self.moq_met,
            "moq_purchase_cost_required": round(self.moq_purchase_cost_required, 2) if self.moq_purchase_cost_required is not None else None,
            "target_cost_per_package": self.target_cost_per_package,
            "budget_variance_per_pkg": round(self.budget_variance_per_pkg, 4) if self.budget_variance_per_pkg is not None else None,
            "over_budget": self.over_budget,
            "budget_check": {
                "is_over_budget": self.over_budget,
                "variance_pct": round(abs((self.total_cost_per_pkg - (self.target_cost_per_package or 1.0)) / max(0.001, self.target_cost_per_package or 1.0)) * 100, 1) if self.target_cost_per_package else 0.0,
                "target_cost_per_pkg": self.target_cost_per_package,
                "actual_cost_per_pkg": round(self.total_cost_per_pkg, 4)
            },
            "price_per_kg_used": round(self.price_per_kg_used, 2),
            "price_per_kg": round(self.price_per_kg_used, 2),
            "price_source": self.price_source,
            "price_last_updated": self.price_last_updated,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "commercial_notes": self.assumptions,
            "included_components": self.included_components,
            "excluded_components": self.excluded_components,
            "breakdown": breakdown_dict
        }


def calculate_packaging_cost(
    material_obj: Any,
    format_type: str = "pouch",
    product_weight_g: float = 100.0,
    package_quantity: int = 5000,
    currency: str = "INR",
    length_cm: Optional[float] = None,
    width_cm: Optional[float] = None,
    height_cm: Optional[float] = None,
    explicit_area_cm2: Optional[float] = None,
    custom_thickness_um: Optional[float] = None,
    layer_count: int = 1,
    closure_cost_per_pkg: Optional[float] = None,
    label_cost_per_pkg: Optional[float] = None,
    printing_cost_per_pkg: Optional[float] = None,
    secondary_pack_cost_per_pkg: Optional[float] = None,
    labor_packing_cost_per_pkg: Optional[float] = None,
    transport_cost_per_pkg: Optional[float] = None,
    wastage_pct_override: Optional[float] = None,
    target_cost_per_package: Optional[float] = None,
    target_total_budget: Optional[float] = None,
) -> CostBreakdown:
    """
    Computes rigorous unit and batch packaging costs for a given material and scenario.
    """
    req_curr = (currency or "INR").upper()
    curr_sym = CURRENCY_SYMBOLS.get(req_curr, req_curr)
    
    assumptions = []
    included_components = ["Raw Polymer/Film Material", "Cutting/Forming Scrap Wastage"]
    excluded_components = ["Tooling / Cylinder Engraving Setup Fees", "Customs Duties & Regional GST/VAT", "Retailer Margin"]

    # 1. Format profile & default parameters
    fmt_key = format_type.lower() if format_type else "pouch"
    fmt_info = FORMAT_DEFAULTS.get(fmt_key, FORMAT_DEFAULTS["pouch"])
    
    # 2. Film Area Calculation
    area_cm2, area_expl = estimate_film_area_cm2(
        format_type=fmt_key,
        product_weight_g=product_weight_g,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        explicit_area_cm2=explicit_area_cm2
    )
    area_m2 = area_cm2 * 1e-4  # 1 m² = 10,000 cm²
    assumptions.append(area_expl)

    # 3. Thickness Calculation (µm)
    # Priority: user override -> material thickness_min or average -> default 35 µm
    mat_thick_min = getattr(material_obj, "thickness_min", None)
    mat_thick_max = getattr(material_obj, "thickness_max", None)
    
    if custom_thickness_um and custom_thickness_um > 0:
        thickness_um = float(custom_thickness_um)
        assumptions.append(f"User custom film gauge: {thickness_um} µm")
    elif mat_thick_min and mat_thick_max:
        thickness_um = (mat_thick_min + mat_thick_max) / 2.0
        assumptions.append(f"Nominal material catalog thickness: {thickness_um:.1f} µm (range {mat_thick_min}-{mat_thick_max} µm)")
    elif mat_thick_min:
        thickness_um = float(mat_thick_min)
        assumptions.append(f"Base material catalog thickness: {thickness_um:.1f} µm")
    else:
        thickness_um = 35.0
        assumptions.append("Default packaging film gauge applied: 35.0 µm")

    # If multi-layer structure
    layers = max(1, layer_count or 1)
    if layers > 1:
        # Combined structure thickness scale
        thickness_um = thickness_um * (1.0 + 0.35 * (layers - 1))
        assumptions.append(f"Multi-layer structure ({layers} plies): combined equivalent gauge {thickness_um:.1f} µm")

    # 4. Material Density (g/cm³)
    mat_density = getattr(material_obj, "material_density_g_cm3", None)
    if not mat_density or mat_density <= 0:
        mtype = getattr(material_obj, "mat_type", "LDPE")
        mat_density = DEFAULT_DENSITIES.get(mtype, 0.95)
        assumptions.append(f"Assumed polymer density for {mtype}: {mat_density:.2f} g/cm³")
    else:
        assumptions.append(f"Material specification density: {mat_density:.2f} g/cm³")

    # 5. Material Mass Calculation (Unit-Safe)
    # Mass (g) = Area (cm²) × Thickness (cm) × Density (g/cm³)
    # Thickness in cm = Thickness (µm) × 10⁻⁴
    thickness_cm = thickness_um * 1e-4
    mass_g = area_cm2 * thickness_cm * mat_density
    mass_kg = mass_g / 1000.0

    # 6. Raw Material Price Resolution (Normalized to requested currency)
    # Check if price_per_kg or cost_index exists on material
    mat_price_kg_native = getattr(material_obj, "price_per_kg", None)
    mat_curr_native = getattr(material_obj, "currency", "INR") or "INR"
    mat_cost_idx = getattr(material_obj, "cost_index", 1.0) or 1.0

    if mat_price_kg_native and mat_price_kg_native > 0:
        # Convert native material price to target currency
        price_per_kg = convert_currency(mat_price_kg_native, mat_curr_native, req_curr)
        price_src = getattr(material_obj, "price_source", "Supplier / Converter Benchmark")
        confidence = getattr(material_obj, "price_confidence", "Medium")
    else:
        # Fallback based on cost_index (where cost_index 1.0 ≈ INR 130/kg baseline LDPE)
        base_inr_price = mat_cost_idx * 130.0
        price_per_kg = convert_currency(base_inr_price, "INR", req_curr)
        price_src = "Estimated from Material Cost Index (Baseline LDPE = ₹130/kg)"
        confidence = "Illustrative Demo"

    # Material raw cost per unit
    raw_material_cost_per_pkg = mass_kg * price_per_kg

    # 7. Wastage & Scrap Rate (%)
    if wastage_pct_override is not None and wastage_pct_override >= 0:
        wastage_pct = float(wastage_pct_override)
        assumptions.append(f"User-specified converting scrap rate: {wastage_pct}%")
    else:
        wastage_pct = getattr(material_obj, "wastage_pct_default", None) or fmt_info["wastage_pct"]
        assumptions.append(f"Standard {fmt_info['label']} converting scrap rate: {wastage_pct}%")
    
    wastage_cost_per_pkg = raw_material_cost_per_pkg * (wastage_pct / 100.0)

    # 8. Operational & Component Costs (Converted to requested currency)
    conv_inr = getattr(material_obj, "conversion_cost_default", None) or fmt_info["conversion_cost_inr"]
    conversion_cost = convert_currency(conv_inr, "INR", req_curr)
    included_components.append("Pouch Forming / Machine Conversion")

    seal_inr = getattr(material_obj, "sealing_cost_default", None) or fmt_info["sealing_cost_inr"]
    sealing_cost = convert_currency(seal_inr, "INR", req_curr)
    included_components.append("Heat / Ultrasonic Sealing Operations")

    # Optional component costs (already passed in requested currency or default to 0)
    printing_cost = float(printing_cost_per_pkg or 0.0)
    if printing_cost > 0:
        included_components.append(f"Custom Printing ({curr_sym}{printing_cost:.2f}/pkg)")

    label_cost = float(label_cost_per_pkg or 0.0)
    if label_cost > 0:
        included_components.append(f"Adhesive Labeling ({curr_sym}{label_cost:.2f}/pkg)")

    closure_cost = float(closure_cost_per_pkg or 0.0)
    if closure_cost > 0:
        included_components.append(f"Closure / Zipper / Valve ({curr_sym}{closure_cost:.2f}/pkg)")

    secondary_pack_cost = float(secondary_pack_cost_per_pkg or 0.0)
    if secondary_pack_cost > 0:
        included_components.append(f"Secondary Shipper Box Share ({curr_sym}{secondary_pack_cost:.2f}/pkg)")

    labor_packing_cost = float(labor_packing_cost_per_pkg or 0.0)
    if labor_packing_cost > 0:
        included_components.append(f"Packing Labor ({curr_sym}{labor_packing_cost:.2f}/pkg)")

    transport_cost = float(transport_cost_per_pkg or 0.0)
    if transport_cost > 0:
        included_components.append(f"Distribution Freight Share ({curr_sym}{transport_cost:.2f}/pkg)")

    # 9. Totals per Package
    total_material_cost_per_pkg = raw_material_cost_per_pkg + wastage_cost_per_pkg
    total_operations_cost_per_pkg = (
        conversion_cost + sealing_cost + printing_cost + label_cost +
        closure_cost + secondary_pack_cost + labor_packing_cost + transport_cost
    )
    total_cost_per_pkg = total_material_cost_per_pkg + total_operations_cost_per_pkg

    # 10. Unit Food Metrics
    prod_w_g = max(1.0, product_weight_g or 100.0)
    prod_w_kg = prod_w_g / 1000.0
    cost_per_kg_food = total_cost_per_pkg / prod_w_kg
    cost_per_100g_food = cost_per_kg_food / 10.0

    # 11. Production Batch Scaling & Volume Discounts
    qty = max(1, package_quantity or 5000)
    batch_consumed_mass_kg = mass_kg * qty
    gross_batch_cost = total_cost_per_pkg * qty

    # Volume Discount Check
    disc_pct = getattr(material_obj, "quantity_discount_pct", 5.0) or 0.0
    # Apply discount only if batch quantity >= 5000 packages
    if qty >= 5000 and disc_pct > 0:
        discount_amount = gross_batch_cost * (disc_pct / 100.0)
        total_batch_cost = gross_batch_cost - discount_amount
        assumptions.append(f"Volume scale discount of {disc_pct:.1f}% applied for production batch of {qty:,} units")
    else:
        disc_pct = 0.0
        discount_amount = 0.0
        total_batch_cost = gross_batch_cost

    # Minimum Order Quantity (MOQ) Check
    moq_kg = getattr(material_obj, "moq_kg", 50.0) or 50.0
    moq_met = batch_consumed_mass_kg >= moq_kg
    moq_purchase_cost_required = None
    if not moq_met:
        # Minimum polymer purchase cost needed to place mill order
        moq_purchase_cost_required = moq_kg * price_per_kg
        assumptions.append(f"Note: Batch consumes {batch_consumed_mass_kg:.1f} kg film; converter minimum order quantity is {moq_kg:.0f} kg ({curr_sym}{moq_purchase_cost_required:.2f}).")

    # 12. Budget Compliance
    over_budget = False
    budget_variance = None
    if target_cost_per_package and target_cost_per_package > 0:
        budget_variance = total_cost_per_pkg - target_cost_per_package
        if budget_variance > 0:
            over_budget = True
    elif target_total_budget and target_total_budget > 0:
        target_per_unit = target_total_budget / qty
        budget_variance = total_cost_per_pkg - target_per_unit
        if budget_variance > 0:
            over_budget = True

    date_updated_str = datetime.utcnow().strftime("%Y-%m-%d")

    return CostBreakdown(
        film_area_cm2=area_cm2,
        film_area_m2=area_m2,
        thickness_microns=thickness_um,
        density_g_cm3=mat_density,
        material_mass_grams=mass_g,
        material_mass_kg=mass_kg,
        currency=req_curr,
        currency_symbol=curr_sym,
        material_cost_per_pkg=raw_material_cost_per_pkg,
        wastage_pct=wastage_pct,
        wastage_cost_per_pkg=wastage_cost_per_pkg,
        conversion_cost_per_pkg=conversion_cost,
        sealing_cost_per_pkg=sealing_cost,
        printing_cost_per_pkg=printing_cost,
        label_cost_per_pkg=label_cost,
        closure_cost_per_pkg=closure_cost,
        secondary_pack_cost_per_pkg=secondary_pack_cost,
        labor_packing_cost_per_pkg=labor_packing_cost,
        transport_cost_per_pkg=transport_cost,
        total_material_cost_per_pkg=total_material_cost_per_pkg,
        total_operations_cost_per_pkg=total_operations_cost_per_pkg,
        total_cost_per_pkg=total_cost_per_pkg,
        product_weight_grams=prod_w_g,
        cost_per_kg_food=cost_per_kg_food,
        cost_per_100g_food=cost_per_100g_food,
        batch_quantity=qty,
        total_batch_material_mass_kg=batch_consumed_mass_kg,
        gross_batch_cost_before_discount=gross_batch_cost,
        quantity_discount_pct=disc_pct,
        quantity_discount_amount=discount_amount,
        total_batch_cost=total_batch_cost,
        moq_kg=moq_kg,
        moq_met=moq_met,
        moq_purchase_cost_required=moq_purchase_cost_required,
        target_cost_per_package=target_cost_per_package,
        budget_variance_per_pkg=budget_variance,
        over_budget=over_budget,
        price_per_kg_used=price_per_kg,
        price_source=price_src,
        price_last_updated=date_updated_str,
        confidence=confidence,
        assumptions=assumptions,
        included_components=included_components,
        excluded_components=excluded_components
    )
