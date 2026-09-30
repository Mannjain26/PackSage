from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.scenario import Scenario, Recommendation, Report, AuditLog
from app.models.material import Material
from app.models.user import User
from app.api.v1.auth import get_current_user, require_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    active = db.query(func.count(Scenario.id)).filter(Scenario.status != "archived").scalar()
    materials_kb = db.query(func.count(Material.id)).filter(Material.verified == True).scalar()
    reports_count = db.query(func.count(Report.id)).scalar()
    pending_review = db.query(func.count(Material.id)).filter(Material.verified == False).scalar()
    return {
        "active_scenarios": active or 0,
        "materials_in_kb": materials_kb or 0,
        "reports_generated": reports_count or 0,
        "pending_material_verification": pending_review or 0,
    }


@router.get("/recent-scenarios")
def recent_scenarios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scenarios = db.query(Scenario).order_by(Scenario.created_at.desc()).limit(5).all()
    return [
        {
            "id": s.id,
            "commodity_name": s.commodity_name,
            "storage_type": s.storage_type,
            "target_shelf_life_days": s.target_shelf_life_days,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
        }
        for s in scenarios
    ]


@router.get("/audit", dependencies=[Depends(require_role("admin", "engineer"))])
def audit_log(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "timestamp": l.timestamp.isoformat(),
        }
        for l in logs
    ]
