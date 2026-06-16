from fastapi import APIRouter

from app.metrics import metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    return {
        "total_shadow_requests": metrics.total,
        "matches": metrics.matches,
        "mismatches": metrics.mismatches,
        "match_rate": metrics.match_rate,
    }
