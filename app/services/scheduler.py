from apscheduler.schedulers.background import BackgroundScheduler
from app.services.report_engine import generate_report
from app.db.database import SessionLocal
from app.models.report import ReportDefinition
import smtplib
from email.message import EmailMessage
import os
from app.services.report_engine import cleanup_old_reports

scheduler = BackgroundScheduler()


def send_email(file_path, to_email):
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

    msg = EmailMessage()
    msg["Subject"] = "Scheduled Jira Report"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg.set_content("Please find attached report.")

    with open(file_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename="report.csv")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)


def run_scheduled_report(report_id):
    db = SessionLocal()

    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id
    ).first()

    if not report:
        return

    result = generate_report({
        "project_keys": report.project_keys,
        "fields": report.fields,
        "statuses": report.statuses,
        "jql_custom": report.jql_custom,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "range_days": report.range_days
    })

    file_path = result["file"]

    if report.email:
        send_email(file_path, report.email)


def schedule_report(report_id, cron_expression):
    # Remove existing job if exists
    if scheduler.get_job(str(report_id)):
        scheduler.remove_job(str(report_id))

    scheduler.add_job(
        run_scheduled_report,
        "cron",
        id=str(report_id),
        replace_existing=True,
        **cron_expression,
        args=[report_id]
    )


def start_scheduler():
    scheduler.start()

def load_existing_jobs():
    from app.db.database import SessionLocal
    from app.models.report import ReportDefinition
    import json

    db = SessionLocal()

    reports = db.query(ReportDefinition).all()

    for report in reports:
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

def start_cleanup_scheduler():
    import threading
    import time

    def run():
        while True:
            cleanup_old_reports(days=7)
            time.sleep(86400)  # run once daily

    thread = threading.Thread(target=run, daemon=True)
    thread.start()