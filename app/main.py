from fastapi import FastAPI
from app.db.database import engine, Base
from app.api import reports, jira
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.services.scheduler import start_scheduler

app = FastAPI()
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.include_router(reports.router)
app.include_router(jira.router)

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})