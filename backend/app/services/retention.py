"""Retention policy – delete expired temporary upload files."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def cleanup_expired_files() -> int:
    """Remove temp files older than UPLOAD_RETENTION_HOURS.

    Returns the number of files deleted.
    """
    temp_dir = Path(settings.UPLOAD_TEMP_DIR)
    if not temp_dir.exists():
        return 0

    max_age_seconds = settings.UPLOAD_RETENTION_HOURS * 3600
    now = time.time()
    deleted = 0

    for file in temp_dir.iterdir():
        if not file.is_file():
            continue
        age = now - file.stat().st_mtime
        if age > max_age_seconds:
            try:
                file.unlink()
                deleted += 1
                logger.info("Deleted expired temp file: %s (age=%.0fs)", file.name, age)
            except OSError:
                logger.warning("Failed to delete temp file: %s", file.name, exc_info=True)

    if deleted:
        logger.info("Retention cleanup: removed %d expired file(s)", deleted)
    return deleted


async def retention_loop(interval_seconds: int = 3600) -> None:
    """Background loop that runs cleanup_expired_files periodically.

    Runs every *interval_seconds* (default: 1 hour).
    Designed to be launched as an asyncio task during app lifespan.
    """
    while True:
        try:
            deleted = await asyncio.to_thread(cleanup_expired_files)
            logger.debug("Retention check complete, deleted=%d", deleted)
        except Exception:
            logger.exception("Error during retention cleanup")
        await asyncio.sleep(interval_seconds)
