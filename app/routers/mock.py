import asyncio

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/mock")


class PromptRequest(BaseModel):
    prompt: str


@router.post("/primary")
async def mock_primary(body: PromptRequest):
    return {"model": "primary", "output": "Paris"}


@router.post("/candidate")
async def mock_candidate(body: PromptRequest, delay_ms: int = 0):
    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000)
    return {"model": "candidate", "output": "Paris"}
