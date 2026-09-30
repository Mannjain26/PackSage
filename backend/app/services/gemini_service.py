"""
PackSage AI — Google Gemini Generative AI Service
==================================================
Uses Google Gemini to generate domain-expert technical explanations,
risk assessments, and packaging recommendations for ranked food packaging materials.
"""

import os
import json
import logging
import warnings
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Suppress library deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception as e:
    logger.warning("google.generativeai import failed: %s", e)
    genai = None
    GENAI_AVAILABLE = False


def _get_api_key() -> Optional[str]:
    return (
        getattr(settings, "GEMINI_API_KEY", "") or
        os.environ.get("GEMINI_API_KEY", "")
    ).strip() or None


def is_gemini_active() -> bool:
    return GENAI_AVAILABLE and bool(_get_api_key())


def generate_gemini_explanations(
    scenario_info: Dict[str, Any],
    requirement_bands: Dict[str, Any],
    top_candidates: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Calls Gemini Generative AI to produce engineering rationales for the top ranked materials.
    Returns a dict mapping material_id (str) -> explanation_text (str).
    """
    api_key = _get_api_key()
    if not api_key or not GENAI_AVAILABLE:
        logger.info("Gemini API key not configured or package unavailable. Using advanced heuristic explanation.")
        return {}

    try:
        genai.configure(api_key=api_key)
        
        # Candidate models to try in order of speed and capability
        models_to_try = [
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-3.5-flash",
            "gemini-pro-latest",
        ]
        model = None
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                break
            except Exception:
                continue

        if not model:
            model = genai.GenerativeModel("gemini-3.8-flash")

        # Prepare summary of candidates
        cand_summaries = []
        for item in top_candidates[:5]:
            mat = item.get("material")
            mat_id = str(getattr(mat, "id", item.get("material_id", "")))
            mat_name = getattr(mat, "name", item.get("material_name", ""))
            polymer = getattr(mat, "mat_type", getattr(mat, "polymer_type", "Standard Polymer"))
            fit_score = item.get("fit_score", 0.0)
            otr = getattr(mat, "otr", "N/A")
            wvtr = getattr(mat, "wvtr", "N/A")
            th = getattr(mat, "thickness_microns", getattr(mat, "thickness_min", 30))
            breathable = getattr(mat, "breathable", False)
            cost = getattr(mat, "cost_index", "N/A")
            sus = getattr(mat, "sustainability_score", "N/A")

            cand_summaries.append({
                "id": mat_id,
                "name": mat_name,
                "polymer": polymer,
                "ml_fit_score": round(fit_score, 3),
                "otr": otr,
                "wvtr": wvtr,
                "thickness_um": th,
                "breathable": breathable,
                "cost_index": cost,
                "sustainability_score": sus
            })

        prompt = f"""
You are an expert food packaging scientist and materials engineer for PackSage AI.
Analyze the following packaging scenario and provide concise, rigorous engineering explanations for each candidate material evaluated by our Scikit-Learn ML engine.

SCENARIO:
- Commodity: {scenario_info.get('commodity_name', 'N/A')} ({scenario_info.get('commodity_category', 'N/A')})
- Storage: {scenario_info.get('storage_type', 'ambient')}
- Target Shelf Life: {scenario_info.get('target_shelf_life_days', 'N/A')} days
- Moisture: {scenario_info.get('moisture_pct', 'N/A')}%
- Respiration Rate: {scenario_info.get('respiration_rate', 'N/A')} mg CO2/kg/hr
- Transport: {scenario_info.get('transport_mode', 'road')} ({scenario_info.get('transport_days', 'N/A')} days)

REQUIREMENTS:
- OTR Target: {requirement_bands.get('otr_target', 'N/A')}
- WVTR Target: {requirement_bands.get('wvtr_target', 'N/A')}
- Thickness Target: {requirement_bands.get('thickness_target_microns', 'N/A')} um
- Notes: {requirement_bands.get('notes', 'N/A')}

CANDIDATES EVALUATED BY SCIKIT-LEARN:
{json.dumps(cand_summaries, indent=2)}

OUTPUT REQUIREMENT:
Respond ONLY with a valid JSON object where keys are the candidate "id" (string) and values are the concise 2-3 paragraph engineering rationale.
Each explanation must address:
1. Barrier compatibility (OTR/WVTR and respiration/moisture management)
2. Practical packaging recommendations (e.g. MAP gas mix, micro-perforations, anti-fog)
3. Trade-offs between ML fit, cost, and sustainability.

Do not include markdown code block syntax around the JSON (or format as pure json).
"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean any markdown json wrapper
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        result_dict = json.loads(text)
        return {str(k): str(v) for k, v in result_dict.items()}

    except Exception as e:
        logger.error("Gemini API call failed: %s", e)
        return {}


def build_fallback_explanation(scenario_info: Dict[str, Any], mat: Any, fit_score: float, ml_traces: List[str]) -> str:
    """
    Generates rich, scientific packaging rationale when Gemini API key is not configured or fails.
    """
    name = getattr(mat, "name", "Material")
    polymer = getattr(mat, "mat_type", getattr(mat, "polymer_type", "Standard Polymer"))
    otr = getattr(mat, "otr", None)
    wvtr = getattr(mat, "wvtr", None)
    th = getattr(mat, "thickness_microns", getattr(mat, "thickness_min", 30))
    breathable = getattr(mat, "breathable", False)
    sus = getattr(mat, "sustainability_score", 50)
    cost = getattr(mat, "cost_index", 2)
    comm = scenario_info.get("commodity_name", "the produce")

    trace_summary = "\n".join(ml_traces)
    
    explanation = (
        f"{name} ({polymer}, {th}um) achieved a Scikit-Learn predicted barrier fit score of {fit_score * 100:.1f}%. "
        f"For {comm}, it provides "
        f"{'breathable gas exchange essential for active respiration' if breathable else f'robust barrier containment with an OTR of {otr} cc/m2/day and WVTR of {wvtr} g/m2/day'}. "
        f"Sustainability is rated at {sus}/100 with a cost index of {cost}/5.\n\n"
        f"ML Inference Trace:\n{trace_summary}\n\n"
        f"[Note: Add GEMINI_API_KEY in backend/.env to activate Google Gemini generative packaging insights.]"
    )
    return explanation
