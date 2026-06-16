import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services import llm_client

logger = logging.getLogger(__name__)
router = APIRouter()


class PromptRequest(BaseModel):
    prompt: str


@router.post("/proxy")
async def proxy(body: PromptRequest, background_tasks: BackgroundTasks):
    try:
        primary_response = await llm_client.call_primary(body.prompt)
    except Exception as e:
        logger.error("Primary LLM call failed: %s", e)
        raise HTTPException(status_code=502, detail="Primary LLM unavailable")

    return primary_response
