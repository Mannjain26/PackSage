"""
Unit tests for Packaging Cost Estimation, Optimization, and Unit-Safety Engine.
"""
import pytest
from types import SimpleNamespace
from app.services.cost_engine import (
    calculate_film_area_cm2,
    calculate_packaging_cost,
    convert_currency,
    FORMAT_DEFAULT_SPECS,
    CURRENCY_RATES_TO_INR
)


def make_mock_material(
    price_per_kg=180.0,
    currency="INR",
    density=0.92,
    moq_kg=100.0,
    discount_pct=5.0,
    price_source="Converter Benchmark",
    price_confidence="high"
):
    return SimpleNamespace(
        id="mat-1",
        name="Test Polymer Film",
        mat_type="LDPE",
        price_per_kg=price_per_kg,
        currency=currency,
        material_density_g_cm3=density,
        price_per_sqm=None,
        price_source=price_source,
        price_last_updated="2026-03-01",
        price_confidence=price_confidence,
        moq_kg=moq_kg,
        quantity_discount_pct=discount_pct,
        wastage_pct_default=5.0,
        conversion_cost_default=0.25,
        sealing_cost_default=0.10,
        thickness_min=30.0,
        thickness_max=50.0
    )


def test_film_area_calculation():
    # Pouch with 20cm x 15cm -> 2 faces = 600 cm2
    pouch_area = calculate_film_area_cm2("pouch", length_cm=20.0, width_cm=15.0)
    assert pouch_area == 600.0

    # Tray with lidding: 18cm x 14cm x 6cm
    tray_area = calculate_film_area_cm2("tray_lidding", length_cm=18.0, width_cm=14.0, height_cm=6.0)
    assert tray_area > 0

    # Default fallback when dimensions not supplied (100g pouch)
    default_pouch_area = calculate_film_area_cm2("pouch", product_weight_g=100.0)
    assert default_pouch_area > 0


def test_unit_safe_film_mass_calculation():
    """
    Mass = Area (cm2) * Thickness (cm) * Density (g/cm3)
    Area = 600 cm2
    Thickness = 50 µm = 0.005 cm
    Density = 0.92 g/cm3 (LDPE)
    Mass = 600 * 0.005 * 0.92 = 2.76 g = 0.00276 kg
    """
    mat = make_mock_material(price_per_kg=165.0, currency="INR", density=0.92)
    res = calculate_packaging_cost(
        material_obj=mat,
        format_type="pouch",
        product_weight_g=100.0,
        package_quantity=10000,
        currency="INR",
        explicit_area_cm2=600.0,
        custom_thickness_um=50.0,
        wastage_pct_override=0.0
    )
    d = res.to_dict()
    assert pytest.approx(d["material_mass_grams"], 0.01) == 2.76
    assert pytest.approx(d["material_mass_kg"], 0.00001) == 0.00276
    # Raw material cost = 0.00276 kg * 165 INR/kg = 0.4554 INR
    assert pytest.approx(d["material_cost_per_pkg"], 0.001) == 0.4554


def test_scrap_wastage_and_operations():
    mat = make_mock_material(price_per_kg=200.0, currency="INR", density=1.0)
    res = calculate_packaging_cost(
        material_obj=mat,
        format_type="pouch",
        product_weight_g=250.0,
        package_quantity=50000,
        currency="INR",
        explicit_area_cm2=1000.0,
        custom_thickness_um=50.0, # 5.0 g mass
        wastage_pct_override=10.0,
        printing_cost_per_pkg=0.15,
        closure_cost_per_pkg=0.05,
        secondary_pack_cost_per_pkg=0.10,
        labor_packing_cost_per_pkg=0.05,
        transport_cost_per_pkg=0.05
    )
    d = res.to_dict()
    assert d["material_cost_per_pkg"] > 0
    assert d["wastage_cost_per_pkg"] > 0
    assert d["total_cost_per_pkg"] > 0
    assert d["cost_per_kg_food"] > 0
    assert d["total_batch_cost"] > 0


def test_currency_conversion():
    inr_val = 100.0
    usd_val = convert_currency(inr_val, "INR", "USD")
    assert pytest.approx(usd_val, 0.01) == 100.0 / CURRENCY_RATES_TO_INR["USD"]

    eur_val = convert_currency(usd_val, "USD", "EUR")
    assert eur_val > 0


def test_minimum_order_quantity_and_discount():
    mat = make_mock_material(price_per_kg=200.0, currency="INR", density=1.0, moq_kg=500.0, discount_pct=10.0)
    res = calculate_packaging_cost(
        material_obj=mat,
        format_type="pouch",
        explicit_area_cm2=1000.0,
        custom_thickness_um=50.0,
        package_quantity=1000
    )
    d = res.to_dict()
    assert d["moq_kg"] == 500.0


def test_budget_compliance_check():
    mat = make_mock_material(price_per_kg=200.0, currency="INR", density=1.0)
    res = calculate_packaging_cost(
        material_obj=mat,
        format_type="pouch",
        explicit_area_cm2=1000.0,
        custom_thickness_um=50.0,
        target_cost_per_package=0.10, # Very low target budget
        package_quantity=10000
    )
    d = res.to_dict()
    assert d["over_budget"] is True

