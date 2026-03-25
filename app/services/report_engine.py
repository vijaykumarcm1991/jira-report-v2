import requests
import os
import csv
import uuid
from datetime import datetime, timedelta
import pytz
import os
from datetime import datetime

progress_store = {}

DATETIME_FORMAT = os.getenv("DATETIME_FORMAT", "%Y-%m-%d %H:%M:%S")
ADD_TZ = os.getenv("ADD_TIMEZONE_SUFFIX", "false").lower() == "true"

IST = pytz.timezone("Asia/Kolkata")

JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")

def build_jql(projects=None, statuses=None, issuetypes=None, custom_jql=None,
              start_date=None, end_date=None, range_days=None):

    if custom_jql:
        return custom_jql

    jql_parts = []

    # Project filter
    if projects:
        proj_str = ",".join([f'"{p}"' for p in projects])
        jql_parts.append(f"project IN ({proj_str})")

    # Status filter
    if statuses:
        status_str = ",".join([f'"{s}"' for s in statuses])
        jql_parts.append(f"status IN ({status_str})")

    # Issue Type filter
    if issuetypes:
        type_str = ",".join([f'"{t}"' for t in issuetypes])
        jql_parts.append(f"issuetype IN ({type_str})")

    # 🔥 Date Logic

    # ✅ Case 1: Last N Days
    if range_days:
        now = datetime.now(IST)
        start = now - timedelta(days=range_days)

        start_str = start.strftime("%Y-%m-%d")
        jql_parts.append(f'created >= "{start_str}"')

    # ✅ Case 2: Fixed Date Range
    elif start_date and end_date:
        jql_parts.append(f'created >= "{start_date}"')

        # Convert end_date → next day
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        next_day = end_dt + timedelta(days=1)
        next_day_str = next_day.strftime("%Y-%m-%d")

        jql_parts.append(f'created < "{next_day_str}"')

    return " AND ".join(jql_parts) if jql_parts else ""

def fetch_issues(jql, fields, job_id=None):
    url = f"{JIRA_URL}/rest/api/2/search"

    start_at = 0
    max_results = 50
    all_issues = []

    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": ",".join(fields)
        }

        response = requests.get(
            url,
            params=params,
            auth=(JIRA_USERNAME, JIRA_PASSWORD),
            headers={"Accept": "application/json"}
        )

        response.raise_for_status()

        data = response.json()
        issues = data.get("issues", [])

        if not issues:
            break

        total = data.get("total", 0)

        all_issues.extend(issues)
        start_at += max_results

        # 🔥 Update progress
        if job_id:
            progress_store[job_id] = {
                "fetched": len(all_issues),
                "total": total
            }

        # Stop condition (important)
        if start_at >= total:
            break

    return all_issues

def format_datetime(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

        formatted = dt.strftime(DATETIME_FORMAT)

        if ADD_TZ:
            formatted += " IST"

        return formatted

    except Exception:
        return value

def extract_field(issue, field):

    field_lower = field.lower()

    # 🔥 Handle special Jira fields (robust)
    if field_lower in ["key", "issuekey"]:
        return issue.get("key")

    if field_lower == "id":
        return issue.get("id")

    value = issue["fields"].get(field)

    # Handle datetime
    if isinstance(value, str) and "T" in value:
        return format_datetime(value)

    if isinstance(value, dict):
        return value.get("name") or value.get("value") or str(value)

    if isinstance(value, list):
        return ", ".join([
            v.get("name") if isinstance(v, dict) else str(v)
            for v in value
        ])

    return value

def generate_csv(issues, fields):
    filename = f"/tmp/report_{uuid.uuid4()}.csv"

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Header
        writer.writerow(fields)

        # Rows
        for issue in issues:
            row = [extract_field(issue, f) for f in fields]
            writer.writerow(row)

    return filename


def generate_report(report_config, job_id=None):

    print("DEBUG CONFIG:", report_config)   # 👈 ADD HERE

    jql = build_jql(
        projects=report_config.get("project_keys"),
        statuses=report_config.get("statuses"),
        issuetypes=report_config.get("issuetypes"),
        custom_jql=report_config.get("jql_custom"),
        start_date=report_config.get("start_date"),
        end_date=report_config.get("end_date"),
        range_days=report_config.get("range_days")
    )

    print("DEBUG JQL:", jql)   # 👈 ADD HERE

    fields = report_config.get("fields", [])

    issues = fetch_issues(jql, fields, job_id)

    file_path = generate_csv(issues, fields)

    return {
        "jql": jql,
        "total_issues": len(issues),
        "file": file_path
    }