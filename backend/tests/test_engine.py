import pytest
from app.services.rule_engine import (
    PackagingRequirements,
    apply_hard_constraints,
    rank_materials,
    optimize_selection,
    generate_recommendations
)
from app.models.material import Material
from app.models.scenario import Scenario

# Mock Materials
m_airtight = Material(id='1', name='Airtight Film', verified=True, food_contact_safe=True, temp_min=-20, temp_max=80, breathable=False, otr=10, wvtr=5, cost_index=1.0, sustainability_score=40)
m_breathable = Material(id='2', name='Breathable Film', verified=True, food_contact_safe=True, temp_min=-10, temp_max=50, breathable=True, otr=None, wvtr=20, cost_index=1.5, sustainability_score=60)
m_unsafe = Material(id='3', name='Unsafe Film', verified=True, food_contact_safe=False, temp_min=-20, temp_max=80, breathable=True, otr=1000, wvtr=20, cost_index=0.8, sustainability_score=80)
m_unverified = Material(id='4', name='Unverified Film', verified=False, food_contact_safe=True, temp_min=-20, temp_max=80, breathable=True, otr=1000, wvtr=20, cost_index=1.0, sustainability_score=50)

def test_stage_1_hard_constraints():
    req = PackagingRequirements(
        temp_min_required=0,
        temp_max_required=30,
        must_be_food_contact_safe=True,
        must_be_breathable=True
    )
    materials = [m_airtight, m_breathable, m_unsafe, m_unverified]
    
    candidates, excluded = apply_hard_constraints(req, materials)
    
    assert len(candidates) == 1
    assert candidates[0].id == '2'
    
    assert len(excluded) == 3
    reasons = {e.material_id: e.reason for e in excluded}
    assert 'airtight' in reasons['1'].lower()
    assert 'safe' in reasons['3'].lower()
    assert 'verified' in reasons['4'].lower()

def test_stage_2_fallback():
    req = PackagingRequirements(otr_max=50, wvtr_max=10)
    materials = [m_airtight]
    
    # 1. Test standard ML ranking mode
    scored_ml, mode_ml = rank_materials(req, materials)
    assert mode_ml == 'ml'
    assert len(scored_ml) == 1
    assert scored_ml[0][1] > 0

    # 2. Test explicit rule fallback mode
    scored_fb, mode_fb = rank_materials(req, materials, force_fallback=True)
    assert mode_fb == 'rule_fallback'
    assert len(scored_fb) == 1
    mat, score, traces = scored_fb[0]
    assert mat.id == '1'
    assert score > 0
    assert len(traces) == 2

def test_stage_3_optimization():
    scored_materials = [
        (m_airtight, 0.9, ['trace1']),
        (m_breathable, 0.5, ['trace2'])
    ]
    
    # Fit heavy
    weights = {'fit': 0.8, 'sustainability': 0.1, 'cost_efficiency': 0.1}
    ranked = optimize_selection(scored_materials, weights)
    assert ranked[0]['material'].id == '1'
    
    # Sustainability heavy
    weights_sus = {'fit': 0.1, 'sustainability': 0.8, 'cost_efficiency': 0.1}
    ranked_sus = optimize_selection(scored_materials, weights_sus)
    # Breathable has higher sus score (60) than Airtight (40)
from unittest.mock import patch

@patch("app.services.rule_engine.generate_gemini_explanations", return_value={})
def test_integration_mango_scenario(mock_gemini):
    # Mock scenario
    s = Scenario(
        commodity_name='Mango',
        commodity_category='fresh_produce',
        storage_type='ambient',
        target_shelf_life_days=4,
        respiration_rate=60.0
    )
    materials = [m_airtight, m_breathable]
    
    res = generate_recommendations(s, materials)
    
    # Should only select breathable film
    assert res.candidates_considered == 2
    assert len(res.final_ranking) == 1
    assert res.final_ranking[0]['material'].id == '2'
    assert len(res.excluded_with_reasons) == 1
    assert res.excluded_with_reasons[0].material_id == '1'
    assert 'airtight' in res.excluded_with_reasons[0].reason.lower()
