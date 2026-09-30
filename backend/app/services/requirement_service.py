from app.models.scenario import CommodityProfile, StorageScenario, PackagingRequirements

class RequirementInferenceEngine:
    @staticmethod
    def infer_requirements(commodity: CommodityProfile, storage: StorageScenario, requirements: PackagingRequirements):
        # Extremely simplified deterministic inference for Phase 1
        
        inferred = {
            "otr_target": {"min": 0, "max": 1000},
            "wvtr_target": {"min": 0, "max": 100},
            "thickness_range": {"min": 20, "max": 150},
            "sealability": "High",
            "mechanical_strength": "Medium",
            "gas_permeability": "Medium",
            "food_contact_required": True,
            "temperature_compatibility": {"min": storage.temp_min_c, "max": storage.temp_max_c}
        }
        
        # Adjust based on product type
        if commodity.respiration_classification in ["High", "Very High"]:
            inferred["otr_target"]["min"] = 3000
            inferred["otr_target"]["max"] = 10000
            inferred["gas_permeability"] = "High"
            
        # Adjust based on moisture
        if commodity.moisture_content_pct and commodity.moisture_content_pct > 80:
            inferred["wvtr_target"]["max"] = 15 # Need better barrier
            
        # Override with explicit targets if provided
        if requirements.target_otr:
            inferred["otr_target"]["max"] = requirements.target_otr
        if requirements.target_wvtr:
            inferred["wvtr_target"]["max"] = requirements.target_wvtr
            
        return inferred
