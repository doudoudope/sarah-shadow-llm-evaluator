import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services import llm_client
from app.services.shadow import run_shadow

logger = logging.getLogger(__name__)
router = APIRouter()


class PromptRequest(BaseModel):
    prompt: str


@router.post("/proxy")
async def proxy(body: PromptRequest, background_tasks: BackgroundTasks):
    request_id = str(uuid.uuid4())

    try:
        primary_response = await llm_client.call_primary(body.prompt)
    except Exception as e:
        logger.error("Primary LLM call failed request_id=%s error=%s", request_id, e)
        raise HTTPException(status_code=502, detail="Primary LLM unavailable")

    primary_output = primary_response.get("output", "")
    background_tasks.add_task(run_shadow, request_id, body.prompt, primary_output)

    return primary_response
