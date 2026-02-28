from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class KeywordBase(BaseModel):
    keyword: str
    source: str = "manual"
    language: str = "en"


class KeywordCreate(KeywordBase):
    pass


class KeywordOut(KeywordBase):
    id: int
    heat_score: float
    trends_score: float
    autocomplete_rank: Optional[int] = None
    search_volume: Optional[int] = None
    competition: Optional[float] = None
    is_rising: bool
    source_count: int
    parent_keyword: Optional[str] = None
    expansion_depth: int
    first_seen: datetime
    last_updated: datetime
    categories: list["CategoryBrief"] = []

    model_config = {"from_attributes": True}


class CategoryBrief(BaseModel):
    category_id: int
    category_name: str
    confidence: float

    model_config = {"from_attributes": True}


class KeywordExpansionRequest(BaseModel):
    seed_keyword: str
    depth: int = 1
    use_autocomplete: bool = True
    use_trends: bool = True
    use_serp: bool = True


class KeywordExpansionResult(BaseModel):
    job_id: int
    seed_keyword: str
    status: str


class KeywordListResponse(BaseModel):
    items: list[KeywordOut]
    total: int
    page: int
    page_size: int


class CompetitorCreate(BaseModel):
    domain: str
    name: str
    sitemap_url: Optional[str] = None


class CompetitorOut(BaseModel):
    id: int
    domain: str
    name: str
    sitemap_url: Optional[str] = None
    last_crawled: Optional[datetime] = None
    total_pages: int
    created_at: datetime

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    job_type: str
    status: str
    seed_keyword: Optional[str] = None
    target: Optional[str] = None
    keywords_found: int
    progress: float
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
