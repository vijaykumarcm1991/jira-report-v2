import requests

from fastapi import APIRouter
from app.services.jira_service import (
    JIRA_PASSWORD,
    JIRA_URL,
    JIRA_USERNAME,
    fetch_fields,
    fetch_projects,
    fetch_statuses
)

router = APIRouter(prefix="/jira", tags=["Jira"])


@router.get("/fields")
def get_fields():
    return fetch_fields()


@router.get("/projects")
def get_projects():
    return fetch_projects()


@router.get("/statuses")
def get_statuses():
    return fetch_statuses()

@router.get("/issuetypes")
def get_issuetypes():
    res = requests.get(
        f"{JIRA_URL}/rest/api/2/issuetype",
        auth=(JIRA_USERNAME, JIRA_PASSWORD),
        headers={"Accept": "application/json"}
    )

    data = res.json()

    return [
        {"name": i.get("name")}
        for i in data
    ]