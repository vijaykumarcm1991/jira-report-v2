import json

from app.models import report
from fastapi import APIRouter
from app.db.database import SessionLocal
from app.models.report import ReportDefinition, ReportHistory
from app.services.report_engine import generate_report
from fastapi.responses import FileResponse
import os
from app.services.report_engine import progress_store
import uuid
from app.services.scheduler import schedule_report
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/")
def create_report(report: dict):
    db = SessionLocal()

    new_report = ReportDefinition(
        name=report["name"],
        project_keys=report.get("project_keys", []),
        fields=report.get("fields", []),
        statuses=report.get("statuses", []),
        issuetypes=report.get("issuetypes", []),
        jql_custom=report.get("jql_custom"),
        start_date=report.get("start_date"),
        end_date=report.get("end_date"),
        range_days=report.get("range_days"),
        email=report.get("email"),
        cron=report.get("cron")
    )

    db.add(new_report)
    db.commit()
    if new_report.cron:
        # Example: {"hour": "*", "minute": "*/5"}
        import json

        if new_report.cron:
            try:
                # Try JSON format first
                cron_dict = json.loads(new_report.cron)

            except Exception:
                # Fallback: parse cron string (e.g. */1 * * * *)
                parts = new_report.cron.split()

                if len(parts) == 5:
                    cron_dict = {
                        "minute": parts[0],
                        "hour": parts[1],
                        "day": parts[2],
                        "month": parts[3],
                        "day_of_week": parts[4],
                    }
                else:
                    raise ValueError("Invalid cron format")

            schedule_report(new_report.id, cron_dict)
    db.refresh(new_report)

    return new_report

@router.get("/")
def list_reports():
    db = SessionLocal()
    return db.query(ReportDefinition).all()

@router.post("/{report_id}/run")
def run_report(report_id: int):
    db = SessionLocal()

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id
    ).first()

    if not report:
        return {"error": "Report not found"}

    result = generate_report({
        "project_keys": report.project_keys,
        "fields": report.fields,
        "statuses": report.statuses,
        "issuetypes": report.issuetypes,
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    }, report_id=report.id)

    return result

@router.get("/{report_id}/download")
def download_report(report_id: int, job_id: str = None):
    db = SessionLocal()

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id
    ).first()

    if not report:
        return {"error": "Report not found"}

    if not job_id:
        job_id = str(uuid.uuid4())

    result = generate_report({
        "project_keys": report.project_keys,
        "fields": report.fields,
        "statuses": report.statuses,
        "issuetypes": report.issuetypes,
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    }, job_id=job_id, report_id=report.id)

    file_path = result["file"]

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(
        path=file_path,
        filename=f"{report.name}.csv",
        media_type="text/csv"
    )

@router.post("/{report_id}/preview")
def preview_report(report_id: int):
    db = SessionLocal()

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id
    ).first()

    if not report:
        return {"error": "Report not found"}

    result = generate_report({
        "project_keys": report.project_keys,
        "fields": report.fields,
        "statuses": report.statuses,
        "issuetypes": report.issuetypes,
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    }, report_id=report.id)

    return {
        "jql": result["jql"],
        "total_issues": result["total_issues"]
    }

@router.put("/{report_id}")
def update_report(report_id: int, updated_data: dict):
    db = SessionLocal()

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id
    ).first()

    if not report:
        return {"error": "Report not found"}

    report.name = updated_data.get("name")
    report.project_keys = updated_data.get("project_keys")
    report.fields = updated_data.get("fields")
    report.statuses = updated_data.get("statuses")
    report.issuetypes = updated_data.get("issuetypes")
    report.start_date = updated_data.get("start_date")
    report.end_date = updated_data.get("end_date")
    report.range_days = updated_data.get("range_days")
    report.email = updated_data.get("email")
    report.cron = updated_data.get("cron")

    if report.cron:
        try:
            cron_dict = json.loads(report.cron)
        except Exception:
            parts = report.cron.split()
            cron_dict = {
                "minute": parts[0],
                "hour": parts[1],
                "day": parts[2],
                "month": parts[3],
                "day_of_week": parts[4],
            }

        schedule_report(report.id, cron_dict)

    db.commit()

    return {"message": "Report updated successfully"}

@router.delete("/{report_id}")
def delete_report(report_id: int):
    db = SessionLocal()

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id
    ).first()

    if not report:
        return {"error": "Report not found"}

    db.delete(report)
    db.commit()

    return {"message": "Report deleted successfully"}

@router.get("/progress/{job_id}")
def get_progress(job_id: str):
    return progress_store.get(job_id, {"fetched": 0, "total": 0})

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    return db.query(ReportHistory).order_by(ReportHistory.id.desc()).all()

@router.get("/history/{id}/download")
def download_history(id: int, db: Session = Depends(get_db)):
    history = db.query(ReportHistory).filter(ReportHistory.id == id).first()

    if not history or not history.file_path:
        return {"error": "File not found"}

    return FileResponse(history.file_path, filename="report.csv")