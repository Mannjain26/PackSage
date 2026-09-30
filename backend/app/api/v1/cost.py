"""
Packaging Cost Estimation & Commercial Calculation API Router
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.services.cost_engine import (
    calculate_packaging_cost,
    FORMAT_DEFAULTS,
    CURRENCY_SYMBOLS,
    CostBreakdown
)

router = APIRouter(prefix="/cost", tags=["cost"])

class CostEstimateRequest(BaseModel):
    material_id: Optional[str] = None
    format_type: str = Field("pouch", description="pouch | bag | sachet | tray_lidding | bottle | jar | box | bulk | custom")
    product_weight_g: float = Field(100.0, ge=0.1, description="Food fill weight in grams per unit")
    package_quantity: int = Field(5000, ge=1, description="Production batch size")
    currency: str = Field("INR", description="INR | USD | EUR")
    
    # Optional geometry
    length_cm: Optional[float] = Field(None, ge=0.0)
    width_cm: Optional[float] = Field(None, ge=0.0)
    height_cm: Optional[float] = Field(None, ge=0.0)
    film_area_cm2: Optional[float] = Field(None, ge=0.0)
    custom_thickness_um: Optional[float] = Field(None, ge=1.0)
    layer_count: int = Field(1, ge=1, le=10)
    
    # Optional secondary costs per package (in requested currency)
    closure_cost_per_pkg: Optional[float] = Field(None, ge=0.0)
    label_cost_per_pkg: Optional[float] = Field(None, ge=0.0)
    printing_cost_per_pkg: Optional[float] = Field(None, ge=0.0)
    secondary_pack_cost_per_pkg: Optional[float] = Field(None, ge=0.0)
    labor_packing_cost_per_pkg: Optional[float] = Field(None, ge=0.0)
    transport_cost_per_pkg: Optional[float] = Field(None, ge=0.0)
    wastage_pct_override: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    # Target budgets
    target_cost_per_package: Optional[float] = Field(None, ge=0.0)
    target_total_budget: Optional[float] = Field(None, ge=0.0)

class BatchCostComparisonRequest(CostEstimateRequest):
    candidate_material_ids: List[str] = Field(..., min_length=1)

@router.get("/formats")
def list_package_formats():
    """Returns available standard packaging formats and default operational assumptions."""
    return {
        "formats": FORMAT_DEFAULTS,
        "currencies": list(CURRENCY_SYMBOLS.keys()),
        "currency_symbols": CURRENCY_SYMBOLS
    }

@router.post("/estimate")
def estimate_material_cost(
    req: CostEstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculates granular unit, batch, food-weight, and operational cost breakdown for a packaging material."""
    if req.material_id:
        mat = db.query(Material).filter(Material.id == req.material_id).first()
        if not mat:
            raise HTTPException(404, f"Material with ID {req.material_id} not found")
    else:
        # Default generic LDPE film benchmark
        mat = db.query(Material).filter(Material.mat_type == "LDPE").first()
        if not mat:
            mat = db.query(Material).first()

    breakdown = calculate_packaging_cost(
        material_obj=mat,
        format_type=req.format_type,
        product_weight_g=req.product_weight_g,
        package_quantity=req.package_quantity,
        currency=req.currency,
        length_cm=req.length_cm,
        width_cm=req.width_cm,
        height_cm=req.height_cm,
        explicit_area_cm2=req.film_area_cm2,
        custom_thickness_um=req.custom_thickness_um,
        layer_count=req.layer_count,
        closure_cost_per_pkg=req.closure_cost_per_pkg,
        label_cost_per_pkg=req.label_cost_per_pkg,
        printing_cost_per_pkg=req.printing_cost_per_pkg,
        secondary_pack_cost_per_pkg=req.secondary_pack_cost_per_pkg,
        labor_packing_cost_per_pkg=req.labor_packing_cost_per_pkg,
        transport_cost_per_pkg=req.transport_cost_per_pkg,
        wastage_pct_override=req.wastage_pct_override,
        target_cost_per_package=req.target_cost_per_package,
        target_total_budget=req.target_total_budget
    )

    return {
        "material_id": mat.id if mat else None,
        "material_name": mat.name if mat else "Generic Polymer Benchmark",
        "cost_breakdown": breakdown.to_dict(),
        "disclaimer": "Cost values are indicative engineering estimates based on active resin indices, geometric envelopes, and converter benchmarks. Actual supplier quotes depend on cylinder tooling, order quantity, payment terms, and regional taxes."
    }

@router.post("/compare-batch")
def compare_materials_cost(
    req: BatchCostComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compares multiple candidate packaging materials under identical production constraints."""
    materials = db.query(Material).filter(Material.id.in_(req.candidate_material_ids)).all()
    if not materials:
        raise HTTPException(400, "None of the provided candidate material IDs were found.")

    comparisons = []
    for m in materials:
        cb = calculate_packaging_cost(
            material_obj=m,
            format_type=req.format_type,
            product_weight_g=req.product_weight_g,
            package_quantity=req.package_quantity,
            currency=req.currency,
            length_cm=req.length_cm,
            width_cm=req.width_cm,
            height_cm=req.height_cm,
            explicit_area_cm2=req.film_area_cm2,
            custom_thickness_um=req.custom_thickness_um,
            layer_count=req.layer_count,
            closure_cost_per_pkg=req.closure_cost_per_pkg,
            label_cost_per_pkg=req.label_cost_per_pkg,
            printing_cost_per_pkg=req.printing_cost_per_pkg,
            secondary_pack_cost_per_pkg=req.secondary_pack_cost_per_pkg,
            labor_packing_cost_per_pkg=req.labor_packing_cost_per_pkg,
            transport_cost_per_pkg=req.transport_cost_per_pkg,
            wastage_pct_override=req.wastage_pct_override,
            target_cost_per_package=req.target_cost_per_package,
            target_total_budget=req.target_total_budget
        )
        comparisons.append({
            "material_id": m.id,
            "material_name": m.name,
            "mat_type": m.mat_type,
            "cost_breakdown": cb.to_dict(),
            "cost_per_pkg": cb.total_cost_per_pkg,
            "cost_per_kg_food": cb.cost_per_kg_food,
            "total_batch_cost": cb.total_batch_cost,
            "confidence": cb.confidence
        })

    comparisons.sort(key=lambda x: x["cost_per_pkg"])

    return {
        "currency": req.currency.upper(),
        "package_quantity": req.package_quantity,
        "product_weight_g": req.product_weight_g,
        "comparisons": comparisons
    }
