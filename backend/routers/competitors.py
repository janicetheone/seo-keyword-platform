import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.competitor import Competitor
from backend.models.competitor_keyword import CompetitorKeyword
from backend.schemas.keyword import CompetitorCreate, CompetitorOut
from backend.services.competitor_analyzer import analyze_competitor, get_keyword_gap

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


@router.get("")
async def list_competitors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).order_by(Competitor.name))
    competitors = result.scalars().all()
    return [
        {
            "id": c.id, "domain": c.domain, "name": c.name,
            "last_crawled": c.last_crawled.isoformat() if c.last_crawled else None,
            "total_pages": c.total_pages,
        }
        for c in competitors
    ]


@router.post("")
async def add_competitor(req: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    competitor = Competitor(
        domain=req.domain,
        name=req.name,
        sitemap_url=req.sitemap_url,
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return {"id": competitor.id, "domain": competitor.domain}


@router.post("/{competitor_id}/analyze")
async def start_analysis(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
):
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        return {"error": "Competitor not found"}

    async def _run():
        from backend.database import async_session
        async with async_session() as session:
            await analyze_competitor(session, competitor_id)

    asyncio.create_task(_run())
    return {"status": "started", "competitor": competitor.domain}


@router.get("/{competitor_id}/keywords")
async def get_competitor_keywords(
    competitor_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetitorKeyword)
        .where(CompetitorKeyword.competitor_id == competitor_id)
        .order_by(CompetitorKeyword.frequency.desc())
        .limit(limit)
    )
    keywords = result.scalars().all()
    return [
        {
            "keyword": ck.keyword, "frequency": ck.frequency,
            "in_title": ck.in_title, "in_h1": ck.in_h1, "in_meta": ck.in_meta,
        }
        for ck in keywords
    ]


@router.get("/{competitor_id}/gap")
async def keyword_gap(competitor_id: int, db: AsyncSession = Depends(get_db)):
    return await get_keyword_gap(db, competitor_id)


@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    competitor = await db.get(Competitor, competitor_id)
    if competitor:
        await db.delete(competitor)
        await db.commit()
    return {"ok": True}
