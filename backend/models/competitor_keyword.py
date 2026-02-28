from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class CompetitorKeyword(Base):
    __tablename__ = "competitor_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(500), nullable=False, index=True)
    source_page = Column(String(1000), nullable=True)
    frequency = Column(Integer, default=1)  # occurrence count across pages
    in_title = Column(Integer, default=0)
    in_h1 = Column(Integer, default=0)
    in_meta = Column(Integer, default=0)
    first_seen = Column(DateTime, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="keywords")
