import logging
from datetime import datetime
from sqlalchemy import select, desc

from backend.database import async_session
from backend.models.keyword import Keyword
from backend.models.collection_job import CollectionJob
from backend.models.trend_snapshot import TrendSnapshot
from backend.services.google_trends import fetch_trends_batched
from backend.services.trending_discovery import fetch_all_trending
from backend.services.keyword_expander import run_expansion

logger = logging.getLogger(__name__)


async def scheduled_trends_refresh():
    """Refresh Google Trends data for top keywords. Runs as a scheduled task."""
    async with async_session() as db:
        result = await db.execute(
            select(Keyword).order_by(desc(Keyword.heat_score)).limit(50)
        )
        keywords = result.scalars().all()
        if not keywords:
            return

        kw_texts = [kw.keyword for kw in keywords]
        trends_data = await fetch_trends_batched(kw_texts)

        for kw in keywords:
            score_key = f"{kw.keyword}_score"
            if score_key in trends_data.get("interest_over_time", {}):
                new_score = trends_data["interest_over_time"][score_key]
                kw.trends_score = new_score
                snapshot = TrendSnapshot(
                    keyword_id=kw.id,
                    trends_score=new_score,
                    is_rising=kw.is_rising,
                )
                db.add(snapshot)

        # Check for newly rising keywords
        for item in trends_data.get("rising", []):
            result = await db.execute(
                select(Keyword).where(Keyword.keyword == item["keyword"])
            )
            kw = result.scalar_one_or_none()
            if kw:
                kw.is_rising = True

        await db.commit()
        logger.info(f"Trends refresh complete for {len(kw_texts)} keywords")


async def scheduled_trending_discovery():
    """Auto-discover and expand trending topics. Runs every 6 hours."""
    logger.info("Starting scheduled trending discovery...")
    data = await fetch_all_trending()

    # Collect unique terms across all sources, prioritise Google
    seen = set()
    terms = []
    for source in ("google", "twitter", "reddit"):
        for item in data.get(source, [])[:8]:
            term = item["term"].strip()
            if term and term.lower() not in seen and len(term) > 2:
                seen.add(term.lower())
                terms.append(term)

    terms = terms[:15]  # process top 15 trending terms
    logger.info(f"Trending discovery: found {len(terms)} unique terms to expand")

    async with async_session() as db:
        for term in terms:
            job = CollectionJob(
                job_type="expansion",
                status="pending",
                seed_keyword=term,
                created_at=datetime.utcnow(),
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            try:
                await run_expansion(
                    db, term,
                    depth=1,
                    use_autocomplete=True,
                    use_trends=False,   # skip to avoid rate limits in bulk
                    use_serp=False,
                    existing_job_id=job.id,
                )
            except Exception as e:
                logger.warning(f"Expansion failed for trending term '{term}': {e}")

    logger.info(f"Trending discovery complete: expanded {len(terms)} terms")
