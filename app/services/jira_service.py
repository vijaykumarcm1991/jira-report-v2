import requests
import os

JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")


def get_auth():
    return (JIRA_USERNAME, JIRA_PASSWORD)


def get_headers():
    return {
        "Accept": "application/json"
    }


# 🔹 Fetch all fields
def fetch_fields():
    url = f"{JIRA_URL}/rest/api/2/field"

    response = requests.get(url, auth=get_auth(), headers=get_headers())
    response.raise_for_status()

    fields = response.json()

    # Return only useful info
    return [
        {
            "id": f["id"],
            "name": f["name"]
        }
        for f in fields
    ]


# 🔹 Fetch projects
def fetch_projects():
    url = f"{JIRA_URL}/rest/api/2/project"

    response = requests.get(url, auth=get_auth(), headers=get_headers())
    response.raise_for_status()

    projects = response.json()

    return [
        {
            "key": p["key"],
            "name": p["name"]
        }
        for p in projects
    ]


# 🔹 Fetch statuses
def fetch_statuses():
    url = f"{JIRA_URL}/rest/api/2/status"

    response = requests.get(url, auth=get_auth(), headers=get_headers())
    response.raise_for_status()

    statuses = response.json()

    return [
        {
            "name": s["name"]
        }
        for s in statuses
    ]