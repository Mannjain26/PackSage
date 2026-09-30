from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class CommodityProfileBase(BaseModel):
    product_name: str
    product_type: str
    commodity_category: str
    moisture_content_pct: Optional[float] = None
    oil_fat_content_pct: Optional[float] = None
    ph_level: Optional[float] = None
    respiration_rate: Optional[float] = None
    respiration_classification: Optional[str] = None

class StorageScenarioBase(BaseModel):
    storage_type: str
    temp_min_c: float
    temp_max_c: float
    temp_target_c: float
    rh_min_pct: float
    rh_max_pct: float
    rh_target_pct: float
    transport_duration_days: Optional[float] = None

class PackagingRequirementsBase(BaseModel):
    target_shelf_life_days: int
    target_otr: Optional[float] = None
    target_wvtr: Optional[float] = None
    food_contact_required: bool = True

class ScenarioCreate(BaseModel):
    name: str
    commodity_profile: CommodityProfileBase
    storage_scenario: StorageScenarioBase
    packaging_requirements: PackagingRequirementsBase

class ScenarioResponse(BaseModel):
    id: UUID
    name: str
    status: str
    owner_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScenarioDetailResponse(ScenarioResponse):
    commodity_profile: Optional[CommodityProfileBase] = None
    storage_scenario: Optional[StorageScenarioBase] = None
    packaging_requirements: Optional[PackagingRequirementsBase] = None
    
    class Config:
        from_attributes = True
