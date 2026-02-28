import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.tasks.expansion_task import scheduled_trends_refresh, scheduled_trending_discovery

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    """Configure and start the background scheduler."""
    # Refresh trends for top keywords daily at 3 AM
    scheduler.add_job(
        scheduled_trends_refresh,
        "cron",
        hour=3,
        minute=0,
        id="daily_trends_refresh",
        replace_existing=True,
    )
    # Auto-discover trending topics every 6 hours
    scheduler.add_job(
        scheduled_trending_discovery,
        "interval",
        hours=6,
        id="trending_discovery",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: daily trends refresh + 6-hour trending discovery")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
