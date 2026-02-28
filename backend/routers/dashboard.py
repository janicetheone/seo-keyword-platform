from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.database import get_db
from backend.models.keyword import Keyword, KeywordCategoryMap
from backend.models.template_category import TemplateCategory
from backend.models.collection_job import CollectionJob
from backend.models.competitor import Competitor
from backend.models.competitor_keyword import CompetitorKeyword

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get summary statistics for the dashboard."""
    # Total keywords
    total = (await db.execute(select(func.count(Keyword.id)))).scalar() or 0

    # New this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_this_week = (await db.execute(
        select(func.count(Keyword.id)).where(Keyword.first_seen >= week_ago)
    )).scalar() or 0

    # Rising count
    rising_count = (await db.execute(
        select(func.count(Keyword.id)).where(Keyword.is_rising == True)
    )).scalar() or 0

    # Categories with counts
    cat_result = await db.execute(
        select(TemplateCategory.name, TemplateCategory.display_name, TemplateCategory.color, func.count(KeywordCategoryMap.id))
        .outerjoin(KeywordCategoryMap)
        .group_by(TemplateCategory.id)
        .order_by(func.count(KeywordCategoryMap.id).desc())
    )
    category_dist = [
        {"name": r[0], "display_name": r[1], "color": r[2], "count": r[3]}
        for r in cat_result.all()
    ]

    # Last job
    last_job_result = await db.execute(
        select(CollectionJob)
        .order_by(desc(CollectionJob.created_at))
        .limit(1)
    )
    last_job = last_job_result.scalar_one_or_none()
    last_collection = None
    if last_job:
        last_collection = {
            "type": last_job.job_type,
            "status": last_job.status,
            "time": last_job.completed_at.isoformat() if last_job.completed_at else last_job.created_at.isoformat(),
        }

    # Average heat score
    avg_heat = (await db.execute(select(func.avg(Keyword.heat_score)))).scalar() or 0

    return {
        "total_keywords": total,
        "new_this_week": new_this_week,
        "rising_count": rising_count,
        "avg_heat_score": round(avg_heat, 1),
        "category_distribution": category_dist,
        "last_collection": last_collection,
    }


@router.get("/top-keywords")
async def get_top_keywords(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get top keywords by heat score."""
    result = await db.execute(
        select(Keyword)
        .order_by(desc(Keyword.heat_score))
        .limit(limit)
    )
    keywords = result.scalars().all()
    return [
        {
            "id": kw.id, "keyword": kw.keyword,
            "heat_score": kw.heat_score, "trends_score": kw.trends_score,
            "is_rising": kw.is_rising, "source": kw.source,
        }
        for kw in keywords
    ]


@router.get("/opportunity-matrix")
async def get_opportunity_matrix(db: AsyncSession = Depends(get_db)):
    """Get data for heat vs competition scatter plot."""
    result = await db.execute(
        select(Keyword)
        .where(Keyword.heat_score > 0)
        .order_by(desc(Keyword.heat_score))
        .limit(200)
    )
    keywords = result.scalars().all()
    return [
        {
            "keyword": kw.keyword,
            "heat_score": kw.heat_score,
            "competition": kw.competition or 0.5,
            "is_rising": kw.is_rising,
        }
        for kw in keywords
    ]


@router.get("/competitor-coverage")
async def get_competitor_coverage(db: AsyncSession = Depends(get_db)):
    """Get keyword count per competitor for bar chart."""
    result = await db.execute(
        select(Competitor.name, func.count(CompetitorKeyword.id))
        .outerjoin(CompetitorKeyword)
        .group_by(Competitor.id)
        .order_by(func.count(CompetitorKeyword.id).desc())
    )
    return [
        {"name": r[0], "keyword_count": r[1]}
        for r in result.all()
    ]
