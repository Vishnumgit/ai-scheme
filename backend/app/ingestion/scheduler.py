"""
Scheduler for periodic scheme ingestion and seed loading.
Runs as an async background task within FastAPI lifespan.
"""
import asyncio
import logging
from app.core.config import settings
from app.ingestion.importer import run_ingestion, load_seed_schemes

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task = None


async def run_periodic_ingestion(interval_hours: int = 24):
    """Periodically check enabled sources for scheme updates."""
    while True:
        try:
            logger.info("Scheduler: starting periodic scheme refresh...")
            await run_ingestion(dry_run=False, incremental=True)
            logger.info("Scheduler: periodic scheme refresh completed.")
        except Exception as e:
            logger.error("Scheduler error during periodic ingestion: %s", e)

        # Sleep for specified interval
        await asyncio.sleep(interval_hours * 3600)


async def start_scheduler():
    """Called on FastAPI application startup."""
    global _scheduler_task
    # Optional seed check on startup
    if settings.SEED_ON_STARTUP:
        try:
            logger.info("SEED_ON_STARTUP is enabled, verifying seed data...")
            await load_seed_schemes(dry_run=False)
        except Exception as e:
            logger.warning("Could not load seeds on startup: %s", e)


async def stop_scheduler():
    """Called on FastAPI application shutdown."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
