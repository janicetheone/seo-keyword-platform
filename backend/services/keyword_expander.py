import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.keyword import Keyword
from backend.models.collection_job import CollectionJob
from backend.services.autocomplete import expand_keyword
from backend.services.google_trends import fetch_trends
from backend.services.related_searches import fetch_related_searches
from backend.services.keyword_classifier import classify_keyword
from backend.services.heat_ranker import calculate_heat_score
from backend.utils.text_processing import deduplicate_keywords

logger = logging.getLogger(__name__)


async def run_expansion(
    db: AsyncSession,
    seed_keyword: str,
    depth: int = 1,
    use_autocomplete: bool = True,
    use_trends: bool = True,
    use_serp: bool = True,
    existing_job_id: int | None = None,
) -> CollectionJob:
    """Run full keyword expansion pipeline for a seed keyword."""
    # Reuse an existing job record (created by the router) or create a new one
    if existing_job_id is not None:
        job = await db.get(CollectionJob, existing_job_id)
        if job is None:
            raise ValueError(f"Job {existing_job_id} not found")
        job.status = "running"
        job.started_at = datetime.utcnow()
        await db.commit()
    else:
        job = CollectionJob(
            job_type="expansion",
            status="running",
            seed_keyword=seed_keyword,
            started_at=datetime.utcnow(),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

    all_discovered = {}  # keyword_text -> {sources, autocomplete_rank, ...}
    try:
        # Step 1: Autocomplete expansion
        if use_autocomplete:
            job.progress = 10
            await db.commit()
            ac_keywords = await expand_keyword(seed_keyword, depth=depth)
            for i, kw in enumerate(ac_keywords):
                if kw not in all_discovered:
                    all_discovered[kw] = {"sources": set(), "autocomplete_rank": None}
                all_discovered[kw]["sources"].add("autocomplete")
                if all_discovered[kw]["autocomplete_rank"] is None:
                    all_discovered[kw]["autocomplete_rank"] = i + 1
            job.progress = 40
            await db.commit()

        # Step 2: Google Trends
        trends_data = {}
        if use_trends:
            job.progress = 50
            await db.commit()
            # Pick top autocomplete keywords + seed for trends
            trends_seeds = [seed_keyword] + list(all_discovered.keys())[:9]
            trends_data = await fetch_trends(trends_seeds[:5])

            # Add related queries from trends
            for parent_kw, related_list in trends_data.get("related_queries", {}).items():
                for kw in related_list:
                    if kw not in all_discovered:
                        all_discovered[kw] = {"sources": set(), "autocomplete_rank": None}
                    all_discovered[kw]["sources"].add("trends")

            # Add rising keywords
            for item in trends_data.get("rising", []):
                kw = item["keyword"]
                if kw not in all_discovered:
                    all_discovered[kw] = {"sources": set(), "autocomplete_rank": None, "is_rising": True}
                all_discovered[kw]["sources"].add("trends")
                all_discovered[kw]["is_rising"] = True

            job.progress = 65
            await db.commit()

        # Step 3: SERP related searches
        if use_serp:
            job.progress = 70
            await db.commit()
            serp_data = await fetch_related_searches(seed_keyword)
            for kw in serp_data.get("related", []) + serp_data.get("people_also_ask", []):
                if kw not in all_discovered:
                    all_discovered[kw] = {"sources": set(), "autocomplete_rank": None}
                all_discovered[kw]["sources"].add("serp")
            job.progress = 80
            await db.commit()

        # Step 4: Save to database
        job.progress = 85
        await db.commit()
        saved_count = 0
        for kw_text, info in all_discovered.items():
            existing = await db.execute(select(Keyword).where(Keyword.keyword == kw_text))
            existing_kw = existing.scalar_one_or_none()

            # Trends score for this keyword
            trends_score = trends_data.get("interest_over_time", {}).get(f"{kw_text}_score", 0)
            is_rising = info.get("is_rising", False)

            if existing_kw:
                existing_kw.source_count = max(existing_kw.source_count, len(info["sources"]))
                if info["autocomplete_rank"] and (not existing_kw.autocomplete_rank or info["autocomplete_rank"] < existing_kw.autocomplete_rank):
                    existing_kw.autocomplete_rank = info["autocomplete_rank"]
                if trends_score > existing_kw.trends_score:
                    existing_kw.trends_score = trends_score
                if is_rising:
                    existing_kw.is_rising = True
                existing_kw.last_updated = datetime.utcnow()
                existing_kw.heat_score = calculate_heat_score(
                    trends_score=existing_kw.trends_score,
                    autocomplete_rank=existing_kw.autocomplete_rank,
                    source_count=existing_kw.source_count,
                    is_rising=existing_kw.is_rising,
                    competition=existing_kw.competition,
                )
            else:
                source_count = len(info["sources"])
                heat = calculate_heat_score(
                    trends_score=trends_score,
                    autocomplete_rank=info["autocomplete_rank"],
                    source_count=source_count,
                    is_rising=is_rising,
                    competition=None,
                )
                new_kw = Keyword(
                    keyword=kw_text,
                    source=",".join(info["sources"]),
                    heat_score=heat,
                    trends_score=trends_score,
                    autocomplete_rank=info["autocomplete_rank"],
                    is_rising=is_rising,
                    parent_keyword=seed_keyword,
                    expansion_depth=depth,
                    source_count=source_count,
                )
                db.add(new_kw)
                saved_count += 1

        await db.commit()

        # Step 5: Classify keywords
        job.progress = 90
        await db.commit()
        result = await db.execute(select(Keyword).where(Keyword.parent_keyword == seed_keyword))
        keywords_to_classify = result.scalars().all()
        for kw in keywords_to_classify:
            await classify_keyword(db, kw)
        await db.commit()

        job.status = "completed"
        job.keywords_found = saved_count
        job.progress = 100
        job.completed_at = datetime.utcnow()
        await db.commit()
        logger.info(f"Expansion job {job.id} completed: {saved_count} new keywords for '{seed_keyword}'")

    except Exception as e:
        logger.error(f"Expansion job failed: {e}")
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        await db.commit()

    return job
