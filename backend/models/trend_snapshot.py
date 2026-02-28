from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    trends_score = Column(Float, default=0.0)
    is_rising = Column(Boolean, default=False)
    rise_percentage = Column(Float, nullable=True)  # e.g. 500 = 500% increase
    snapshot_date = Column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="trend_snapshots")
