import logging

from fastapi import FastAPI

from app.config import settings
from app.routers import health, mock, proxy

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

app = FastAPI(title="Shadow LLM Evaluator")

app.include_router(health.router)
app.include_router(mock.router)
app.include_router(proxy.router)


@app.on_event("startup")
async def startup():
    logger.info("Shadow LLM Evaluator started")
