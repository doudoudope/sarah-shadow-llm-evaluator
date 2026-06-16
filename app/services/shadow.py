import json
import logging
from datetime import datetime, timezone

from app.metrics import metrics
from app.services import llm_client
from app.utils.comparison import compare
from app.utils.json_extract import extract_json

logger = logging.getLogger(__name__)


async def run_shadow(request_id: str, prompt: str, primary_output: str) -> None:
    try:
        candidate_response = await llm_client.call_candidate(prompt)
        candidate_output = candidate_response.get("output", "")

        extracted_primary = extract_json(primary_output)
        extracted_candidate = extract_json(candidate_output)

        if extracted_primary is not None and extracted_candidate is not None:
            matched = compare(extracted_primary, extracted_candidate)
        else:
            matched = primary_output == candidate_output

        log_entry = {
            "event": "shadow_result",
            "request_id": request_id,
            "prompt": prompt,
            "primary_output": primary_output,
            "candidate_output": candidate_output,
            "extracted_primary_json": extracted_primary,
            "extracted_candidate_json": extracted_candidate,
            "matched": matched,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if matched:
            logger.info(json.dumps(log_entry))
            await metrics.record_match()
        else:
            logger.warning(json.dumps(log_entry))
            await metrics.record_mismatch()

    except Exception as e:
        logger.error(json.dumps({
            "event": "shadow_error",
            "request_id": request_id,
            "prompt": prompt,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))
        await metrics.record_mismatch()
