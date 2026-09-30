import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.scenario import Recommendation, RecommendationItem, Report, Scenario, AuditLog
from app.models.material import Material
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.services.report_generator import generate_pdf_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate/{recommendation_id}", status_code=201)
def generate_report(
    recommendation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(404, "Recommendation not found")

    scenario = db.query(Scenario).filter(Scenario.id == rec.scenario_id).first()
    if not scenario:
        raise HTTPException(404, "Associated scenario not found")
    if scenario.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to generate reports for this scenario")

    items_with_material = []
    for item in sorted(rec.items, key=lambda x: x.rank):
        m = db.query(Material).filter(Material.id == item.material_id).first()
        if m:
            items_with_material.append({
                "rank": item.rank,
                "fit_score": item.fit_score,
                "material": m,
                "explanation_text": item.explanation_text,
            })

    shelf_life = {
        "min": rec.shelf_life_est_min,
        "max": rec.shelf_life_est_max,
        "dominant_failure_mode": rec.dominant_failure_mode,
    }

    # Generate PDF
    report = Report(
        recommendation_id=rec.id,
        qr_code_value=rec.report_uuid,
        generated_by=current_user.id,
    )
    db.add(report)
    db.flush()

    base_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    file_path = generate_pdf_report(
        report_id=report.id,
        report_uuid=rec.report_uuid,
        scenario=scenario,
        ranked_items=items_with_material,
        shelf_life=shelf_life,
        req_notes=[],
        base_url=base_url,
    )

    report.file_path = file_path
    db.add(AuditLog(
        user_id=current_user.id,
        action="REPORT_GENERATED",
        entity_type="report",
        entity_id=report.id,
    ))
    db.commit()
    db.refresh(report)

    return {"report_id": report.id, "file_path": file_path, "qr_code_value": rec.report_uuid}


@router.get("")
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = db.query(Report).order_by(Report.generated_at.desc()).all()
    out = []
    for r in reports:
        rec = db.query(Recommendation).filter(Recommendation.id == r.recommendation_id).first()
        scenario = db.query(Scenario).filter(Scenario.id == rec.scenario_id).first() if rec else None
        
        # Scope reports to owner unless admin/engineer
        if scenario and scenario.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
            continue

        out.append({
            "id": r.id,
            "recommendation_id": r.recommendation_id,
            "scenario_name": scenario.commodity_name if scenario else "Unknown",
            "scenario_id": scenario.id if scenario else None,
            "report_type": r.report_type,
            "qr_code_value": r.qr_code_value,
            "generated_at": r.generated_at.isoformat(),
            "sign_off_status": r.sign_off_status,
            "has_file": bool(r.file_path and os.path.exists(r.file_path)),
        })
    return out


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    
    rec = db.query(Recommendation).filter(Recommendation.id == r.recommendation_id).first()
    scenario = db.query(Scenario).filter(Scenario.id == rec.scenario_id).first() if rec else None
    if scenario and scenario.user_id != current_user.id and current_user.role not in ["admin", "engineer"]:
        raise HTTPException(403, "You do not have permission to download this report")

    if not r.file_path or not os.path.exists(r.file_path):
        raise HTTPException(404, "Report file not found. Please regenerate.")
    return FileResponse(
        r.file_path,
        media_type="application/pdf",
        filename=f"PackSage_Report_{r.qr_code_value[:8]}.pdf",
    )
