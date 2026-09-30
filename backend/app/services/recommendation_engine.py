from typing import List, Dict, Any
from app.models.scenario import Scenario
from app.models.material import Material
from app.services.requirement_service import RequirementInferenceEngine
from app.services.rule_engine import RuleEngine
from sqlalchemy.orm import Session
import json

class RecommendationEngine:
    @staticmethod
    def generate_recommendations(db: Session, scenario: Scenario):
        # 1. Infer requirements
        inferred = RequirementInferenceEngine.infer_requirements(
            scenario.commodity_profile,
            scenario.storage_scenario,
            scenario.packaging_requirements
        )
        
        # 2. Get all available verified materials
        materials = db.query(Material).all()
        
        results = []
        
        # 3. Rule Engine Filtering
        for mat in materials:
            traces = RuleEngine.evaluate_material(mat, inferred)
            
            if RuleEngine.is_eligible(traces):
                # 4. MVP Scoring (Cost vs Performance)
                base_score = 70
                
                # Bonus for better barrier if required
                if inferred.get("wvtr_target", {}).get("max", 9999) < 20 and getattr(mat, "wvtr", 100) < 10:
                    base_score += 15
                    
                # Sustainability bonus
                if getattr(mat, "recyclable", False):
                    base_score += 10
                    
                score = min(99, base_score)
                
                results.append({
                    "material_id": mat.id,
                    "material_name": mat.name,
                    "score": score,
                    "cost": getattr(mat, "cost_per_unit", 0.05),
                    "confidence": "High" if score > 85 else "Medium",
                    "explanation": [t.dict() for t in traces]
                })
                
        # 5. Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "scenario_id": scenario.id,
            "inferred_requirements": inferred,
            "recommendations": results[:10] # Top 10
        }
