"""Background sync task for glucose data."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from sweetwatch.db.engine import SessionLocal
from sweetwatch.services.glucose import glucose_service

logger = logging.getLogger(__name__)


async def sync_glucose_loop() -> None:
    """Background loop to sync glucose data from LibreLinkUp.

    Interval adapts to trend:
    - Stable (trend=3): 3 minutes
    - Rising/Falling: 1 minute
    """
    INTERVAL_STABLE = 3 * 60  # 3 minutes
    INTERVAL_CHANGING = 1 * 60  # 1 minute

    # Wait a bit before first sync to let the app start
    await asyncio.sleep(10)

    while True:
        interval = INTERVAL_STABLE
        try:
            logger.info("Starting glucose sync...")
            db = SessionLocal()
            try:
                stored = await glucose_service.fetch_and_store(db, count=50)
                if stored:
                    logger.info(f"Synced {len(stored)} new glucose readings")
                else:
                    logger.info("No new readings to sync")

                # Check latest trend to determine next interval
                current = glucose_service.get_current(db)
                if current:
                    logger.info(f"Current: {current.value} mg/dL, trend={current.trend}, time={current.timestamp}")
                    if current.trend != 3:  # Not stable
                        interval = INTERVAL_CHANGING
                        logger.info(f"Trend changing, next sync in 1 min")
            finally:
                db.close()
        except Exception as e:
            logger.exception(f"Error syncing glucose data: {e}")

        logger.info(f"Next sync in {interval} seconds")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for background tasks."""
    # Start background sync task
    task = asyncio.create_task(sync_glucose_loop())
    logger.info("Started glucose sync background task")

    yield

    # Cancel background task on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Close glucose service
    await glucose_service.close()
    logger.info("Stopped glucose sync background task")
