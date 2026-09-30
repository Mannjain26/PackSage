import pytest
from app.services.rule_engine import (
    PackagingRequirements,
    infer_requirements,
    apply_hard_constraints,
    rank_materials,
    generate_recommendations,
)
from app.models.material import Material
from app.models.scenario import Scenario

# Realistic test materials
m_ldpe = Material(
    id='mat-ldpe-30',
    name='LDPE Film 30µm',
    mat_type='LDPE',
    verified=True,
    food_contact_safe=True,
    temp_min=-60.0,
    temp_max=80.0,
    breathable=False,
    sealability=True,
    otr=8000.0,
    wvtr=15.0,
    cost_index=1.0,
    sustainability_score=45.0,
)

m_met_pet = Material(
    id='mat-metpet-12',
    name='Met-PET 12µm',
    mat_type='metalized',
    verified=True,
    food_contact_safe=True,
    temp_min=-60.0,
    temp_max=130.0,
    breathable=False,
    sealability=True,
    otr=2.0,
    wvtr=0.3,
    cost_index=2.5,
    sustainability_score=30.0,
)

m_alu_foil = Material(
    id='mat-alu-foil',
    name='Alu Foil Laminate 45µm',
    mat_type='foil_laminate',
    verified=True,
    food_contact_safe=True,
    temp_min=-60.0,
    temp_max=120.0,
    breathable=False,
    sealability=True,
    otr=0.01,
    wvtr=0.01,
    cost_index=3.5,
    sustainability_score=20.0,
)

m_breathable_bopp = Material(
    id='mat-micro-bopp',
    name='Micro-perf BOPP 20µm',
    mat_type='breathable',
    verified=True,
    food_contact_safe=True,
    temp_min=-10.0,
    temp_max=40.0,
    breathable=True,
    sealability=True,
    otr=None,
    wvtr=8.0,
    cost_index=1.5,
    sustainability_score=55.0,
)

m_freezer_film = Material(
    id='mat-freezer-pe',
    name='Heavy Duty PE Freezer Film 60µm',
    mat_type='LDPE',
    verified=True,
    food_contact_safe=True,
    temp_min=-40.0,
    temp_max=60.0,
    breathable=False,
    sealability=True,
    otr=4000.0,
    wvtr=8.0,
    cost_index=1.2,
    sustainability_score=45.0,
)


def test_dry_food_requirement_inference():
    """Dry food requires low WVTR to prevent moisture absorption and caking."""
    req = infer_requirements(
        commodity_category="dry",
        moisture_pct=3.0,
        fat_pct=1.0,
        ph=6.5,
        respiration_rate=None,
        storage_type="ambient",
        target_rh=60.0,
        target_shelf_life_days=180,
    )
    assert req.wvtr_max is not None
    assert req.wvtr_max <= 2.0  # Strict moisture barrier
    assert req.otr_max == 50.0  # Standard dry barrier
    assert req.must_be_breathable is False


def test_oil_rich_food_fat_oxidation_rule():
    """High fat content (>15%) triggers tight oxygen barrier (OTR <= 5) and rancidity protection."""
    req = infer_requirements(
        commodity_category="oily",
        moisture_pct=2.0,
        fat_pct=35.0,  # e.g. Potato Chips / Fried Snack
        ph=6.0,
        respiration_rate=None,
        storage_type="ambient",
        target_rh=50.0,
        target_shelf_life_days=120,
    )
    assert req.otr_max <= 5.0
    assert any("lipid oxidation" in note.lower() or "oxygen barrier" in note.lower() for note in req.notes)


def test_fresh_produce_respiration_screening():
    """Fresh tomato / strawberry with active respiration must exclude airtight films."""
    s = Scenario(
        commodity_name="Fresh Tomato",
        commodity_category="fresh_produce",
        storage_type="chilled",
        target_shelf_life_days=14,
        respiration_rate=55.0,  # High respiration
        moisture_pct=94.0,
    )
    materials = [m_ldpe, m_met_pet, m_breathable_bopp]
    res = generate_recommendations(s, materials)

    assert res.candidates_considered == 3
    # Airtight materials (LDPE, Met-PET) must be excluded for high respiration
    assert any("airtight" in str(e.reason).lower() for e in res.excluded_with_reasons)
    # Breathable film should be the selected candidate
    assert len(res.final_ranking) == 1
    assert res.final_ranking[0]["material"].id == "mat-micro-bopp"


def test_frozen_storage_temperature_envelope():
    """Frozen commodity requires materials capable of tolerating down to -25°C."""
    req = infer_requirements(
        commodity_category="processed",
        moisture_pct=75.0,
        fat_pct=2.0,
        ph=6.5,
        respiration_rate=None,
        storage_type="frozen",
        target_rh=80.0,
        target_shelf_life_days=180,
    )
    assert req.temp_min_required == -25.0
    assert req.thickness_min >= 50.0  # Cold crack resistance floor
