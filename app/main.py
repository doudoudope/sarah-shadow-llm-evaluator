import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import health, metrics, mock, proxy

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Shadow LLM Evaluator started")
    yield


app = FastAPI(title="Shadow LLM Evaluator", lifespan=lifespan)

app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(mock.router)
app.include_router(proxy.router)
