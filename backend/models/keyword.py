from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(500), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False)  # autocomplete, trends, serp, manual, competitor
    heat_score = Column(Float, default=0.0)
    trends_score = Column(Float, default=0.0)
    autocomplete_rank = Column(Integer, nullable=True)
    search_volume = Column(Integer, nullable=True)  # from Google Ads API (future)
    competition = Column(Float, nullable=True)  # 0-1 competition score
    is_rising = Column(Boolean, default=False)
    language = Column(String(10), default="en")
    parent_keyword = Column(String(500), nullable=True)
    expansion_depth = Column(Integer, default=0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_count = Column(Integer, default=1)  # how many sources found this keyword

    categories = relationship("KeywordCategoryMap", back_populates="keyword", cascade="all, delete-orphan")
    trend_snapshots = relationship("TrendSnapshot", back_populates="keyword", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Keyword '{self.keyword}' heat={self.heat_score}>"


class KeywordCategoryMap(Base):
    __tablename__ = "keyword_category_map"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("template_categories.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, default=1.0)  # 0-1 classification confidence
    method = Column(String(20), default="rule")  # rule, tfidf, manual

    keyword = relationship("Keyword", back_populates="categories")
    category = relationship("TemplateCategory", back_populates="keywords")
