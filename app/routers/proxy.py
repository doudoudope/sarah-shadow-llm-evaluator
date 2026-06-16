import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services import llm_client

logger = logging.getLogger(__name__)
router = APIRouter()


class PromptRequest(BaseModel):
    prompt: str


@router.post("/proxy")
async def proxy(request: Request, body: PromptRequest):
    request_id = str(uuid.uuid4())

    try:
        primary_response = await llm_client.call_primary(body.prompt)
    except Exception as e:
        logger.error("Primary LLM call failed request_id=%s error=%s", request_id, e)
        raise HTTPException(status_code=502, detail="Primary LLM unavailable")

    primary_output = primary_response.get("output", "")
    request.app.state.shadow_queue.put_nowait({
        "request_id": request_id,
        "prompt": body.prompt,
        "primary_output": primary_output,
    })

    return primary_response
