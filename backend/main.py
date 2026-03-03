import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, text

from backend.database import init_db, async_session, engine
from backend.models import *  # noqa: ensure all models registered
from backend.models.template_category import TemplateCategory
from backend.models.competitor import Competitor
from backend.models.keyword import Keyword
from backend.routers import keywords, trends, competitors, dashboard, jobs, admin
from backend.tasks.scheduler import setup_scheduler, shutdown_scheduler
from backend.utils.seed_data import TEMPLATE_CATEGORIES, PRESET_COMPETITORS
from backend.config import SEED_KEYWORDS
from backend.services.keyword_classifier import classify_keyword
from backend.services.heat_ranker import calculate_heat_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"


async def run_migrations():
    """Add new columns that may not exist in older DBs."""
    migrations = [
        ("cpc", "REAL"),
        ("competition_index", "INTEGER"),
        ("monthly_searches", "TEXT"),
    ]
    async with engine.begin() as conn:
        for col, typedef in migrations:
            try:
                await conn.execute(text(f"ALTER TABLE keywords ADD COLUMN {col} {typedef}"))
                logger.info(f"Migration: added column keywords.{col}")
            except Exception:
                pass  # column already exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await run_migrations()
    await seed_initial_data()
    setup_scheduler()
    logger.info("SEO Keyword Platform started")
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(title="SEO Keyword Platform", lifespan=lifespan)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# API routers
app.include_router(keywords.router)
app.include_router(trends.router)
app.include_router(competitors.router)
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(admin.router)


async def seed_initial_data():
    """Seed template categories, preset competitors, and seed keywords if empty."""
    async with async_session() as db:
        # Seed categories
        existing = await db.execute(select(TemplateCategory).limit(1))
        if not existing.scalar_one_or_none():
            for cat_data in TEMPLATE_CATEGORIES:
                db.add(TemplateCategory(**cat_data))
            await db.commit()
            logger.info(f"Seeded {len(TEMPLATE_CATEGORIES)} template categories")

        # Seed competitors
        existing = await db.execute(select(Competitor).limit(1))
        if not existing.scalar_one_or_none():
            for comp_data in PRESET_COMPETITORS:
                db.add(Competitor(**comp_data))
            await db.commit()
            logger.info(f"Seeded {len(PRESET_COMPETITORS)} preset competitors")

        # Auto-seed keywords if DB is empty (e.g. after Railway redeploy)
        existing_kw = await db.execute(select(Keyword).limit(1))
        if not existing_kw.scalar_one_or_none():
            logger.info("Keywords table empty — auto-seeding...")
            inserted = 0
            for kw_text in SEED_KEYWORDS:
                kw = Keyword(
                    keyword=kw_text,
                    source="seed",
                    heat_score=calculate_heat_score(trends_score=0, source_count=1),
                    trends_score=0,
                    source_count=1,
                    expansion_depth=0,
                    first_seen=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                )
                db.add(kw)
                await db.flush()
                await classify_keyword(db, kw)
                inserted += 1
            await db.commit()
            logger.info(f"Auto-seeded {inserted} keywords")


# ─── Page routes (Jinja2 templates) ───

@app.get("/")
async def page_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/keywords")
async def page_keywords_list(request: Request):
    return templates.TemplateResponse("keywords/list.html", {"request": request})


@app.get("/keywords/discover")
async def page_keywords_discover(request: Request):
    return templates.TemplateResponse("keywords/discover.html", {"request": request})


@app.get("/keywords/{keyword_id}")
async def page_keyword_detail(request: Request, keyword_id: int):
    return templates.TemplateResponse("keywords/detail.html", {"request": request, "keyword_id": keyword_id})


@app.get("/categories")
async def page_categories(request: Request):
    return templates.TemplateResponse("categories/overview.html", {"request": request})


@app.get("/competitors")
async def page_competitors(request: Request):
    return templates.TemplateResponse("competitors/overview.html", {"request": request})


@app.get("/competitors/{competitor_id}")
async def page_competitor_detail(request: Request, competitor_id: int):
    return templates.TemplateResponse("competitors/detail.html", {"request": request, "competitor_id": competitor_id})


@app.get("/trending")
async def page_trending(request: Request):
    return templates.TemplateResponse("trending.html", {"request": request})


@app.get("/jobs")
async def page_jobs(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})
