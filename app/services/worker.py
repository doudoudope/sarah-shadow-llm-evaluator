import asyncio
import logging

from app.services.shadow import run_shadow

logger = logging.getLogger(__name__)


async def shadow_worker(queue: asyncio.Queue) -> None:
    logger.info("Shadow worker started")
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        try:
            await run_shadow(item["request_id"], item["prompt"], item["primary_output"])
        except Exception as e:
            logger.error("Worker unhandled error: %s", e)
        finally:
            queue.task_done()
    logger.info("Shadow worker stopped")
