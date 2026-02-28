from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from backend.database import Base


class CollectionJob(Base):
    __tablename__ = "collection_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(50), nullable=False)  # expansion, trends, competitor_crawl
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    seed_keyword = Column(String(500), nullable=True)
    target = Column(String(500), nullable=True)  # competitor domain or keyword
    keywords_found = Column(Integer, default=0)
    progress = Column(Float, default=0.0)  # 0-100
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
