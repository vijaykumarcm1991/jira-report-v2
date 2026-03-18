from fastapi import FastAPI
from app.db.database import engine, Base
from app.api import reports, jira

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(reports.router)
app.include_router(jira.router)

@app.get("/")
def home():
    return {"message": "Jira Report V2 running 🚀"}