import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.metrics import metrics
from app.routers import health
from app.routers import metrics as metrics_router
from app.routers import mock, proxy
from app.services.worker import shadow_worker

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    queue = asyncio.Queue(maxsize=settings.shadow_queue_maxsize)
    app.state.shadow_queue = queue
    worker_task = asyncio.create_task(shadow_worker(queue))
    logger.info("Shadow LLM Evaluator started")
    yield
    await queue.put(None)
    await queue.join()
    await worker_task
    await metrics.close()


app = FastAPI(title="Shadow LLM Evaluator", lifespan=lifespan)

app.include_router(health.router)
app.include_router(metrics_router.router)
app.include_router(mock.router)
app.include_router(proxy.router)
