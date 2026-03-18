from fastapi import APIRouter
from app.services.jira_service import (
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