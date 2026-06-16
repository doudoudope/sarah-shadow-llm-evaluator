from fastapi import APIRouter

from app.metrics import metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    return await metrics.get_stats()
