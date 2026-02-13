"""Background sync task for glucose data."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from sweetwatch.db.engine import SessionLocal
from sweetwatch.services.glucose import glucose_service

logger = logging.getLogger(__name__)


async def sync_glucose_loop(interval_minutes: int = 5) -> None:
    """Background loop to sync glucose data from LibreLinkUp."""
    # Wait a bit before first sync to let the app start
    await asyncio.sleep(10)

    while True:
        try:
            db = SessionLocal()
            try:
                stored = await glucose_service.fetch_and_store(db, count=50)
                if stored:
                    logger.info(f"Synced {len(stored)} new glucose readings")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error syncing glucose data: {e}")

        await asyncio.sleep(interval_minutes * 60)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for background tasks."""
    # Start background sync task
    task = asyncio.create_task(sync_glucose_loop(interval_minutes=5))
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
