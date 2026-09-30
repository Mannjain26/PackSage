from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class MaterialBase(BaseModel):
    name: str
    family: str
    material_type: str
    thickness_um: Optional[float] = None
    otr: Optional[float] = None
    wvtr: Optional[float] = None
    tensile_strength: Optional[float] = None
    food_contact_approved: bool = False
    recyclability_score: Optional[float] = None
    cost_per_kg: Optional[float] = None
    status: str = "Draft"

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(MaterialBase):
    name: Optional[str] = None
    family: Optional[str] = None
    material_type: Optional[str] = None
    status: Optional[str] = None

class MaterialResponse(MaterialBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
