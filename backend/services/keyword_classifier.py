import re
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.keyword import Keyword, KeywordCategoryMap
from backend.models.template_category import TemplateCategory

logger = logging.getLogger(__name__)


async def classify_keyword(db: AsyncSession, keyword: Keyword) -> list[dict]:
    """Classify a keyword into template categories using rule-based matching."""
    result = await db.execute(select(TemplateCategory))
    categories = result.scalars().all()
    matches = []

    for cat in categories:
        patterns = json.loads(cat.patterns)
        best_confidence = 0.0

        for pattern in patterns:
            try:
                match = re.search(pattern, keyword.keyword, re.IGNORECASE)
                if match:
                    # Confidence based on how much of the keyword the pattern covers
                    matched_len = match.end() - match.start()
                    coverage = matched_len / max(len(keyword.keyword), 1)
                    confidence = min(0.5 + coverage, 1.0)
                    best_confidence = max(best_confidence, confidence)
            except re.error:
                continue

        if best_confidence > 0:
            matches.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "confidence": round(best_confidence, 3),
            })

    # Save top matches (confidence > 0.3)
    for m in matches:
        if m["confidence"] >= 0.3:
            existing = await db.execute(
                select(KeywordCategoryMap).where(
                    KeywordCategoryMap.keyword_id == keyword.id,
                    KeywordCategoryMap.category_id == m["category_id"],
                )
            )
            if not existing.scalar_one_or_none():
                mapping = KeywordCategoryMap(
                    keyword_id=keyword.id,
                    category_id=m["category_id"],
                    confidence=m["confidence"],
                    method="rule",
                )
                db.add(mapping)

    return matches


async def classify_all_keywords(db: AsyncSession):
    """Re-classify all keywords in the database."""
    result = await db.execute(select(Keyword))
    keywords = result.scalars().all()
    count = 0
    for kw in keywords:
        matches = await classify_keyword(db, kw)
        if matches:
            count += 1
    await db.commit()
    logger.info(f"Classified {count}/{len(keywords)} keywords")
    return count
