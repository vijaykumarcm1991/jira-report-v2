import os
import json
import uuid
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.models.report import ReportDefinition, ReportHistory
from app.services.report_engine import generate_report, progress_store
from app.services.scheduler import schedule_report
import pytz

IST = pytz.timezone("Asia/Kolkata")

# 🔥 Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


# -------------------------------
# CREATE REPORT
# -------------------------------
@router.post("/")
def create_report(report: dict):
    db = SessionLocal()
    try:
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
        db.refresh(new_report)

        # 🔥 Schedule if cron exists
        if new_report.cron:
            try:
                cron_dict = json.loads(new_report.cron)
            except Exception:
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

        return new_report

    finally:
        db.close()


# -------------------------------
# LIST REPORTS
# -------------------------------
@router.get("/")
def list_reports():
    db = SessionLocal()
    try:
        return db.query(ReportDefinition).all()
    finally:
        db.close()


# -------------------------------
# RUN REPORT
# -------------------------------
@router.post("/{report_id}/run")
def run_report(report_id: int):
    db = SessionLocal()
    try:
        report = db.query(ReportDefinition).filter(
            ReportDefinition.id == report_id
        ).first()

        if not report:
            return {"error": "Report not found"}

        logger.info(f"Manual run triggered for report_id={report_id}")

        return generate_report({
            "project_keys": report.project_keys,
            "fields": report.fields,
            "statuses": report.statuses,
            "issuetypes": report.issuetypes,
            "jql_custom": report.jql_custom,
            "start_date": report.start_date,
            "end_date": report.end_date,
            "range_days": report.range_days
        }, report_id=report.id)

    finally:
        db.close()


# -------------------------------
# DOWNLOAD (OPTIMIZED)
# -------------------------------
@router.get("/{id}/download")
def download_report(id: int, job_id: str = None, db: Session = Depends(get_db)):

    logger.info(f"Download requested for report_id={id}")

    # Step 1: Get report
    report = db.query(ReportDefinition).filter(ReportDefinition.id == id).first()
    if not report:
        return {"error": "Report not found"}

    # Step 2: Get latest SUCCESS history
    history = db.query(ReportHistory)\
        .filter(
            ReportHistory.report_id == id,
            ReportHistory.status == "Success"
        )\
        .order_by(ReportHistory.id.desc())\
        .first()

    # Step 3: Reuse if recent
    if history and history.file_path and os.path.exists(history.file_path):
        created_at = history.created_at

        # Make created_at IST-aware if naive
        if created_at.tzinfo is None:
            created_at = IST.localize(created_at)

        now_ist = datetime.now(IST)

        age = now_ist - created_at

        if age < timedelta(hours=1):
            logger.info(f"Using cached report for report_id={id}")

            return FileResponse(
                history.file_path,
                filename=f"{report.name}.csv",
                media_type="text/csv"
            )

    # Step 4: Generate new
    logger.info(f"Generating new report for report_id={id}")

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

    file_path = result.get("file")

    if not file_path or not os.path.exists(file_path):
        return {"error": "File generation failed"}

    return FileResponse(
        file_path,
        filename=f"{report.name}.csv",
        media_type="text/csv"
    )


# -------------------------------
# PREVIEW
# -------------------------------
@router.post("/{report_id}/preview")
def preview_report(report_id: int):
    db = SessionLocal()
    try:
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

    finally:
        db.close()


# -------------------------------
# UPDATE REPORT
# -------------------------------
@router.put("/{report_id}")
def update_report(report_id: int, updated_data: dict):
    db = SessionLocal()
    try:
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

    finally:
        db.close()


# -------------------------------
# DELETE REPORT
# -------------------------------
@router.delete("/{report_id}")
def delete_report(report_id: int):
    db = SessionLocal()
    try:
        report = db.query(ReportDefinition).filter(
            ReportDefinition.id == report_id
        ).first()

        if not report:
            return {"error": "Report not found"}

        db.delete(report)
        db.commit()

        return {"message": "Report deleted successfully"}

    finally:
        db.close()


# -------------------------------
# PROGRESS
# -------------------------------
@router.get("/progress/{job_id}")
def get_progress(job_id: str):
    return progress_store.get(job_id, {"fetched": 0, "total": 0})


# -------------------------------
# HISTORY
# -------------------------------
@router.get("/history")
def get_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(ReportHistory)\
        .order_by(ReportHistory.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


# -------------------------------
# HISTORY DOWNLOAD
# -------------------------------
@router.get("/history/{id}/download")
def download_history(id: int, db: Session = Depends(get_db)):
    history = db.query(ReportHistory).filter(ReportHistory.id == id).first()

    if not history or not history.file_path:
        return {"error": "File not found"}

    return FileResponse(
        history.file_path,
        filename=f"report_{history.report_id}.csv"
    )


# -------------------------------
# RETRY FAILED REPORT
# -------------------------------
@router.post("/history/{id}/retry")
def retry_report(id: int, db: Session = Depends(get_db)):

    history = db.query(ReportHistory).filter(ReportHistory.id == id).first()
    if not history:
        return {"error": "History not found"}

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == history.report_id
    ).first()

    if not report:
        return {"error": "Original report not found"}

    logger.info(f"Retry triggered for report_id={report.id}")

    generate_report({
        "project_keys": report.project_keys,
        "fields": report.fields,
        "statuses": report.statuses,
        "issuetypes": report.issuetypes,
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    }, report_id=report.id)

    return {"message": "Retry triggered"}