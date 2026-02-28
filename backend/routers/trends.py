import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.database import get_db
from backend.models.keyword import Keyword
from backend.models.collection_job import CollectionJob
from backend.models.trend_snapshot import TrendSnapshot
from backend.services.google_trends import fetch_trends_batched
from backend.services.trending_discovery import fetch_all_trending
from backend.services.keyword_expander import run_expansion

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/rising")
async def get_rising_keywords(
    limit: int = Query(20, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get top rising keywords."""
    result = await db.execute(
        select(Keyword)
        .where(Keyword.is_rising == True)
        .order_by(desc(Keyword.heat_score))
        .limit(limit)
    )
    keywords = result.scalars().all()
    return [
        {
            "id": kw.id, "keyword": kw.keyword,
            "heat_score": kw.heat_score, "trends_score": kw.trends_score,
        }
        for kw in keywords
    ]


@router.get("/snapshots/{keyword_id}")
async def get_trend_snapshots(keyword_id: int, db: AsyncSession = Depends(get_db)):
    """Get trend history for a keyword."""
    result = await db.execute(
        select(TrendSnapshot)
        .where(TrendSnapshot.keyword_id == keyword_id)
        .order_by(TrendSnapshot.snapshot_date)
    )
    snapshots = result.scalars().all()
    return [
        {
            "date": s.snapshot_date.isoformat(),
            "score": s.trends_score,
            "is_rising": s.is_rising,
        }
        for s in snapshots
    ]


@router.post("/refresh")
async def refresh_trends(
    keywords: list[str] | None = None,
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
):
    """Refresh trend data for top keywords or specified keywords."""
    if not keywords:
        result = await db.execute(
            select(Keyword).order_by(desc(Keyword.heat_score)).limit(limit)
        )
        kw_objects = result.scalars().all()
        keywords = [kw.keyword for kw in kw_objects]

    if not keywords:
        return {"error": "No keywords to refresh"}

    data = await fetch_trends_batched(keywords)
    updated = 0
    for kw_text in keywords:
        score_key = f"{kw_text}_score"
        if score_key in data.get("interest_over_time", {}):
            result = await db.execute(select(Keyword).where(Keyword.keyword == kw_text))
            kw = result.scalar_one_or_none()
            if kw:
                kw.trends_score = data["interest_over_time"][score_key]
                # Save snapshot
                snapshot = TrendSnapshot(
                    keyword_id=kw.id,
                    trends_score=kw.trends_score,
                    is_rising=kw.is_rising,
                )
                db.add(snapshot)
                updated += 1

    await db.commit()
    return {"updated": updated, "rising_found": len(data.get("rising", []))}


@router.get("/trending-now")
async def get_trending_now():
    """Fetch real-time trending topics from Google, Reddit, and Twitter."""
    data = await fetch_all_trending()
    return data


@router.post("/expand-trending")
async def expand_trending_topics(
    terms: list[str],
    db: AsyncSession = Depends(get_db),
):
    """Start keyword expansion jobs for a list of trending terms."""
    if not terms:
        return {"error": "No terms provided"}

    jobs = []
    for term in terms[:10]:  # cap at 10 concurrent expansions
        job = CollectionJob(
            job_type="expansion",
            status="pending",
            seed_keyword=term,
            created_at=datetime.utcnow(),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        captured_id = job.id

        async def _run(jid=captured_id, kw=term):
            from backend.database import async_session
            async with async_session() as session:
                await run_expansion(
                    session, kw,
                    depth=1,
                    use_autocomplete=True,
                    use_trends=True,
                    use_serp=False,   # skip SERP to keep it fast for bulk runs
                    existing_job_id=jid,
                )

        asyncio.create_task(_run())
        jobs.append({"job_id": job.id, "term": term})

    return {"started": len(jobs), "jobs": jobs}
