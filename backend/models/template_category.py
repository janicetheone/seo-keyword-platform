from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class TemplateCategory(Base):
    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    patterns = Column(Text, nullable=False)  # JSON array of regex patterns
    template_suggestions = Column(Text, nullable=False)  # JSON array of template ideas
    color = Column(String(7), default="#6366f1")  # hex color for UI

    keywords = relationship("KeywordCategoryMap", back_populates="category", cascade="all, delete-orphan")
