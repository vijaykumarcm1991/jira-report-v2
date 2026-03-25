from fastapi import FastAPI
from app.db.database import engine, Base
from app.api import reports, jira
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.services.scheduler import start_scheduler, load_existing_jobs
from jinja2 import Environment, FileSystemLoader
import os

app = FastAPI()
# templates = Jinja2Templates(directory="templates")

template_env = Environment(
    loader=FileSystemLoader("/app/templates")
)

templates = Jinja2Templates(directory="/app/templates")
templates.env.cache = {}   # prevent cache corruption

Base.metadata.create_all(bind=engine)

app.include_router(reports.router)
app.include_router(jira.router)

@app.on_event("startup")
def startup_event():
    start_scheduler()
    load_existing_jobs()

# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

@app.get("/")
def home(request: Request):
    template = template_env.get_template("index.html")
    html_content = template.render()
    return HTMLResponse(content=html_content)