"""
Admin endpoints for managing categories and reseed operations.
"""
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.database import get_db
from backend.models.template_category import TemplateCategory
from backend.models.keyword import Keyword, KeywordCategoryMap
from backend.models.collection_job import CollectionJob
from backend.services.keyword_classifier import classify_all_keywords, classify_keyword
from backend.services.heat_ranker import calculate_heat_score
from backend.services.keyword_expander import run_expansion
from backend.utils.seed_data import TEMPLATE_CATEGORIES
from backend.config import SEED_KEYWORDS

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reseed-categories")
async def reseed_categories(
    reclassify: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuild template categories from seed_data.py without touching keywords.
    - Deletes old category-keyword mappings
    - Upserts all categories (add new, update existing, remove obsolete)
    - Optionally re-runs classifier on all keywords
    """
    new_names = {c["name"] for c in TEMPLATE_CATEGORIES}

    # 1. Clear all keyword-category mappings (will be re-created by classifier)
    await db.execute(delete(KeywordCategoryMap))

    # 2. Remove categories that no longer exist in seed data
    old_cats = (await db.execute(select(TemplateCategory))).scalars().all()
    old_names = {c.name for c in old_cats}
    obsolete = old_names - new_names
    for cat in old_cats:
        if cat.name in obsolete:
            await db.delete(cat)

    await db.commit()

    # 3. Upsert each category from seed data
    upserted = 0
    for cat_data in TEMPLATE_CATEGORIES:
        existing = (
            await db.execute(select(TemplateCategory).where(TemplateCategory.name == cat_data["name"]))
        ).scalar_one_or_none()

        if existing:
            existing.display_name = cat_data["display_name"]
            existing.description = cat_data["description"]
            existing.patterns = cat_data["patterns"]
            existing.template_suggestions = cat_data["template_suggestions"]
            existing.color = cat_data["color"]
        else:
            db.add(TemplateCategory(**cat_data))
        upserted += 1

    await db.commit()

    # 4. Optionally re-classify all keywords with new patterns
    classified = 0
    if reclassify:
        classified = await classify_all_keywords(db)

    return {
        "categories_upserted": upserted,
        "obsolete_removed": len(obsolete),
        "keywords_reclassified": classified,
        "categories": [c["name"] for c in TEMPLATE_CATEGORIES],
    }


@router.post("/populate-seeds")
async def populate_seeds(
    expand: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    1. Insert all SEED_KEYWORDS into DB (skip existing).
    2. Classify each one into the 15 categories.
    3. Optionally kick off async expansion jobs for all seeds.
    """
    inserted = 0
    skipped = 0

    for kw_text in SEED_KEYWORDS:
        existing = (
            await db.execute(select(Keyword).where(Keyword.keyword == kw_text))
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        kw = Keyword(
            keyword=kw_text,
            source="seed",
            heat_score=calculate_heat_score(
                trends_score=0,
                autocomplete_rank=None,
                source_count=1,
                is_rising=False,
                competition=None,
            ),
            trends_score=0,
            source_count=1,
            parent_keyword=None,
            expansion_depth=0,
            first_seen=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )
        db.add(kw)
        await db.flush()
        await classify_keyword(db, kw)
        inserted += 1

    await db.commit()

    # Optionally start expansion jobs for all seeds in background
    jobs_started = 0
    if expand:
        for kw_text in SEED_KEYWORDS:
            job = CollectionJob(
                job_type="expansion",
                status="pending",
                seed_keyword=kw_text,
                created_at=datetime.utcnow(),
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

            captured_id = job.id

            async def _run(jid=captured_id, seed=kw_text):
                from backend.database import async_session
                async with async_session() as session:
                    await run_expansion(
                        session, seed,
                        depth=1,
                        use_autocomplete=True,
                        use_trends=False,
                        use_serp=False,
                        existing_job_id=jid,
                    )

            asyncio.create_task(_run())
            jobs_started += 1

    return {
        "inserted": inserted,
        "skipped": skipped,
        "expansion_jobs_started": jobs_started,
        "total_seeds": len(SEED_KEYWORDS),
    }


@router.get("/categories")
async def list_categories_admin(db: AsyncSession = Depends(get_db)):
    """List all categories with pattern count and keyword count."""
    cats = (await db.execute(select(TemplateCategory))).scalars().all()
    result = []
    for cat in cats:
        kw_count = (
            await db.execute(
                select(KeywordCategoryMap).where(KeywordCategoryMap.category_id == cat.id)
            )
        ).scalars().all()
        result.append({
            "name": cat.name,
            "display_name": cat.display_name,
            "color": cat.color,
            "pattern_count": len(json.loads(cat.patterns)),
            "keyword_count": len(kw_count),
        })
    return result
