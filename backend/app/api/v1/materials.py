from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.models.scenario import AuditLog
from app.models.user import User
from app.api.v1.auth import get_current_user, require_role

router = APIRouter(prefix="/materials", tags=["materials"])


class MaterialCreate(BaseModel):
    name: str
    mat_type: str
    otr: Optional[float] = None
    wvtr: Optional[float] = None
    thickness_min: Optional[float] = None
    thickness_max: Optional[float] = None
    temp_min: Optional[float] = -40.0
    temp_max: Optional[float] = 60.0
    sealability: bool = True
    breathable: bool = False
    food_contact_safe: bool = False
    recyclable: bool = False
    biodegradable: bool = False
    cost_index: float = 1.0
    sustainability_score: float = 50.0
    notes: Optional[str] = None

class MaterialOut(BaseModel):
    id: str
    name: str
    mat_type: str
    otr: Optional[float]
    wvtr: Optional[float]
    thickness_min: Optional[float]
    thickness_max: Optional[float]
    temp_min: Optional[float]
    temp_max: Optional[float]
    sealability: bool
    breathable: bool
    food_contact_safe: bool
    recyclable: bool
    biodegradable: bool
    cost_index: float
    sustainability_score: float
    notes: Optional[str]
    verified: bool
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("", response_model=List[MaterialOut])
def list_materials(
    search: Optional[str] = Query(None),
    mat_type: Optional[str] = Query(None),
    food_contact: Optional[bool] = Query(None),
    recyclable: Optional[bool] = Query(None),
    verified_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Material)
    if search:
        q = q.filter(Material.name.ilike(f"%{search}%"))
    if mat_type:
        q = q.filter(Material.mat_type == mat_type)
    if food_contact is not None:
        q = q.filter(Material.food_contact_safe == food_contact)
    if recyclable is not None:
        q = q.filter(Material.recyclable == recyclable)
    if verified_only:
        q = q.filter(Material.verified == True)
    return q.order_by(Material.name).all()


@router.get("/{material_id}", response_model=MaterialOut)
def get_material(material_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "Material not found")
    return m


@router.post("", response_model=MaterialOut, status_code=201)
def create_material(
    payload: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "engineer")),
):
    m = Material(**payload.dict())
    db.add(m)
    db.add(AuditLog(user_id=current_user.id, action="MATERIAL_CREATED", entity_type="material", entity_id=m.id))
    db.commit()
    db.refresh(m)
    return m


@router.put("/{material_id}", response_model=MaterialOut)
def update_material(
    material_id: str,
    payload: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "engineer")),
):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "Material not found")
    for k, v in payload.dict().items():
        setattr(m, k, v)
    m.updated_at = datetime.utcnow()
    db.add(AuditLog(user_id=current_user.id, action="MATERIAL_UPDATED", entity_type="material", entity_id=m.id))
    db.commit()
    db.refresh(m)
    return m


@router.post("/{material_id}/verify", response_model=MaterialOut)
def verify_material(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "engineer")),
):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "Material not found")
    m.verified = True
    m.updated_at = datetime.utcnow()
    db.add(AuditLog(user_id=current_user.id, action="MATERIAL_VERIFIED", entity_type="material", entity_id=m.id))
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{material_id}", status_code=200)
def delete_material(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "Material not found")
    db.delete(m)
    db.add(AuditLog(user_id=current_user.id, action="MATERIAL_DELETED", entity_type="material", entity_id=material_id))
    db.commit()
    return {"message": "Material deleted successfully", "id": material_id}
