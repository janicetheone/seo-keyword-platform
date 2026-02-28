"""
Manual script to seed initial data (categories, competitors, and optionally run first expansion).
Usually not needed as main.py auto-seeds on startup.

Usage: python -m scripts.seed_initial_data
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import init_db, async_session
from backend.models.template_category import TemplateCategory
from backend.models.competitor import Competitor
from backend.utils.seed_data import TEMPLATE_CATEGORIES, PRESET_COMPETITORS
from sqlalchemy import select


async def main():
    await init_db()
    async with async_session() as db:
        # Seed categories
        existing = await db.execute(select(TemplateCategory).limit(1))
        if not existing.scalar_one_or_none():
            for cat_data in TEMPLATE_CATEGORIES:
                db.add(TemplateCategory(**cat_data))
            await db.commit()
            print(f"Seeded {len(TEMPLATE_CATEGORIES)} template categories")
        else:
            print("Categories already exist, skipping")

        # Seed competitors
        existing = await db.execute(select(Competitor).limit(1))
        if not existing.scalar_one_or_none():
            for comp_data in PRESET_COMPETITORS:
                db.add(Competitor(**comp_data))
            await db.commit()
            print(f"Seeded {len(PRESET_COMPETITORS)} competitors")
        else:
            print("Competitors already exist, skipping")

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
