from sqlalchemy import Column, Integer, String, JSON, DateTime
from app.db.database import Base
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

datetime.now(IST)

class ReportDefinition(Base):
    __tablename__ = "report_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    project_keys = Column(JSON)
    fields = Column(JSON)
    statuses = Column(JSON)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    range_days = Column(Integer, nullable=True)
    email = Column(String, nullable=True)
    cron = Column(String, nullable=True)
    jql_custom = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))