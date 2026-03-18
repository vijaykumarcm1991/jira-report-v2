from app.models import report
from fastapi import APIRouter
from app.db.database import SessionLocal
from app.models.report import ReportDefinition
from app.services.report_engine import generate_report
from fastapi.responses import FileResponse
import os
from app.services.report_engine import progress_store
import uuid

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/")
def create_report(report: dict):
    db = SessionLocal()

    new_report = ReportDefinition(
        name=report["name"],
        project_keys=report.get("project_keys", []),
        fields=report.get("fields", []),
        statuses=report.get("statuses", []),
        jql_custom=report.get("jql_custom"),
        start_date=report.get("start_date"),
        end_date=report.get("end_date"),
        range_days=report.get("range_days")
    )

    db.add(new_report)
    db.commit()
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
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    })

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
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    }, job_id=job_id)

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
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    })

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
    report.start_date = updated_data.get("start_date")
    report.end_date = updated_data.get("end_date")
    report.range_days = updated_data.get("range_days")

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