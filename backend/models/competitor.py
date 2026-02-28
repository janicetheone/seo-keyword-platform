from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    sitemap_url = Column(String(500), nullable=True)
    last_crawled = Column(DateTime, nullable=True)
    total_pages = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    pages = relationship("CompetitorPage", back_populates="competitor", cascade="all, delete-orphan")
    keywords = relationship("CompetitorKeyword", back_populates="competitor", cascade="all, delete-orphan")


class CompetitorPage(Base):
    __tablename__ = "competitor_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(1000), nullable=False)
    title = Column(String(500), nullable=True)
    meta_description = Column(Text, nullable=True)
    h1 = Column(Text, nullable=True)
    h2s = Column(Text, nullable=True)  # JSON array
    crawled_at = Column(DateTime, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="pages")
