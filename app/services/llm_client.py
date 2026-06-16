import httpx

from app.config import settings


async def call_primary(prompt: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.primary_llm_url,
            json={"prompt": prompt},
        )
        response.raise_for_status()
        return response.json()


async def call_candidate(prompt: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.candidate_llm_url,
            json={"prompt": prompt},
            timeout=settings.candidate_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
