import asyncio
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.database import get_db
from backend.models.keyword import Keyword, KeywordCategoryMap
from backend.models.template_category import TemplateCategory
from backend.models.collection_job import CollectionJob
from backend.services.keyword_expander import run_expansion
from backend.services.keyword_classifier import classify_all_keywords
from backend.schemas.keyword import (
    KeywordOut, KeywordExpansionRequest, KeywordExpansionResult, KeywordListResponse
)

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=KeywordListResponse)
async def list_keywords(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    sort_by: str = Query("heat_score"),
    sort_dir: str = Query("desc"),
    category: str | None = None,
    search: str | None = None,
    source: str | None = None,
    rising_only: bool = False,
    parent_keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Keyword)

    if search:
        query = query.where(Keyword.keyword.contains(search))
    if source:
        query = query.where(Keyword.source.contains(source))
    if rising_only:
        query = query.where(Keyword.is_rising == True)
    if parent_keyword:
        query = query.where(Keyword.parent_keyword == parent_keyword)
    if category:
        query = query.join(KeywordCategoryMap).join(TemplateCategory).where(
            TemplateCategory.name == category
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    sort_col = getattr(Keyword, sort_by, Keyword.heat_score)
    if sort_dir == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(sort_col)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    keywords = result.scalars().all()

    items = []
    for kw in keywords:
        cat_maps = await db.execute(
            select(KeywordCategoryMap, TemplateCategory)
            .join(TemplateCategory)
            .where(KeywordCategoryMap.keyword_id == kw.id)
        )
        cats = [
            {"category_id": m.KeywordCategoryMap.category_id, "category_name": m.TemplateCategory.name, "confidence": m.KeywordCategoryMap.confidence}
            for m in cat_maps.all()
        ]
        items.append(KeywordOut(
            id=kw.id, keyword=kw.keyword, source=kw.source,
            heat_score=kw.heat_score, trends_score=kw.trends_score,
            autocomplete_rank=kw.autocomplete_rank, search_volume=kw.search_volume,
            competition=kw.competition, is_rising=kw.is_rising,
            source_count=kw.source_count, parent_keyword=kw.parent_keyword,
            expansion_depth=kw.expansion_depth,
            first_seen=kw.first_seen, last_updated=kw.last_updated,
            categories=cats,
        ))

    return KeywordListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/expand", response_model=KeywordExpansionResult)
async def expand_keywords(
    req: KeywordExpansionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a keyword expansion job in the background."""
    job = CollectionJob(
        job_type="expansion",
        status="pending",
        seed_keyword=req.seed_keyword,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    captured_job_id = job.id

    async def _run():
        from backend.database import async_session
        async with async_session() as session:
            await run_expansion(
                session, req.seed_keyword,
                depth=req.depth,
                use_autocomplete=req.use_autocomplete,
                use_trends=req.use_trends,
                use_serp=req.use_serp,
                existing_job_id=captured_job_id,
            )

    asyncio.create_task(_run())

    return KeywordExpansionResult(
        job_id=job.id,
        seed_keyword=req.seed_keyword,
        status="started",
    )


@router.post("/classify-all")
async def reclassify_all(db: AsyncSession = Depends(get_db)):
    count = await classify_all_keywords(db)
    return {"classified": count}


@router.get("/export")
async def export_csv(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Export keywords as CSV."""
    query = select(Keyword)
    if category:
        query = query.join(KeywordCategoryMap).join(TemplateCategory).where(
            TemplateCategory.name == category
        )
    query = query.order_by(desc(Keyword.heat_score))
    result = await db.execute(query)
    keywords = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["keyword", "heat_score", "trends_score", "source", "is_rising", "autocomplete_rank", "source_count", "first_seen"])
    for kw in keywords:
        writer.writerow([
            kw.keyword, kw.heat_score, kw.trends_score, kw.source,
            kw.is_rising, kw.autocomplete_rank, kw.source_count,
            kw.first_seen.isoformat() if kw.first_seen else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=keywords_export.csv"},
    )


@router.get("/{keyword_id}")
async def get_keyword_detail(keyword_id: int, db: AsyncSession = Depends(get_db)):
    kw = await db.get(Keyword, keyword_id)
    if not kw:
        return {"error": "not found"}
    cat_maps = await db.execute(
        select(KeywordCategoryMap, TemplateCategory)
        .join(TemplateCategory)
        .where(KeywordCategoryMap.keyword_id == kw.id)
    )
    cats = [
        {"category_id": m.KeywordCategoryMap.category_id, "category_name": m.TemplateCategory.display_name, "confidence": m.KeywordCategoryMap.confidence}
        for m in cat_maps.all()
    ]
    return {
        "id": kw.id, "keyword": kw.keyword, "source": kw.source,
        "heat_score": kw.heat_score, "trends_score": kw.trends_score,
        "autocomplete_rank": kw.autocomplete_rank, "is_rising": kw.is_rising,
        "source_count": kw.source_count, "parent_keyword": kw.parent_keyword,
        "competition": kw.competition, "search_volume": kw.search_volume,
        "first_seen": kw.first_seen.isoformat() if kw.first_seen else None,
        "last_updated": kw.last_updated.isoformat() if kw.last_updated else None,
        "categories": cats,
    }


@router.delete("/{keyword_id}")
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    kw = await db.get(Keyword, keyword_id)
    if kw:
        await db.delete(kw)
        await db.commit()
    return {"ok": True}
