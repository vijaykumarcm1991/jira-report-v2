from apscheduler.schedulers.background import BackgroundScheduler
from app.services.report_engine import generate_report
from app.db.database import SessionLocal
from app.models.report import ReportDefinition
import smtplib
from email.message import EmailMessage
import os

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
    scheduler.add_job(
        run_scheduled_report,
        "cron",
        id=str(report_id),
        **cron_expression,
        args=[report_id]
    )


def start_scheduler():
    scheduler.start()