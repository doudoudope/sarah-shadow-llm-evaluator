import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.metrics import metrics


@pytest.fixture(autouse=True)
def reset_metrics():
    metrics.total = 0
    metrics.matches = 0
    metrics.mismatches = 0
    yield


async def test_proxy_returns_primary_response():
    with patch("app.services.llm_client.call_primary", new_callable=AsyncMock) as mock_primary, \
         patch("app.services.llm_client.call_candidate", new_callable=AsyncMock) as mock_candidate:
        mock_primary.return_value = {"model": "primary", "output": "Paris"}
        mock_candidate.return_value = {"model": "candidate", "output": "Paris"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            r = await client.post("/proxy", json={"prompt": "What is the capital of France?"})

    assert r.status_code == 200
    assert r.json() == {"model": "primary", "output": "Paris"}


async def test_proxy_fast_when_candidate_slow():
    async def slow_candidate(prompt):
        await asyncio.sleep(0.5)
        return {"model": "candidate", "output": "Paris"}

    with patch("app.services.llm_client.call_primary", new_callable=AsyncMock) as mock_primary, \
         patch("app.services.llm_client.call_candidate", side_effect=slow_candidate):
        mock_primary.return_value = {"model": "primary", "output": "Paris"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            r = await client.post("/proxy", json={"prompt": "test"})

    assert r.status_code == 200
    assert r.json()["model"] == "primary"


async def test_candidate_failure_does_not_fail_proxy():
    with patch("app.services.llm_client.call_primary", new_callable=AsyncMock) as mock_primary, \
         patch("app.services.llm_client.call_candidate", side_effect=Exception("candidate down")):
        mock_primary.return_value = {"model": "primary", "output": "Paris"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            r = await client.post("/proxy", json={"prompt": "test"})

    assert r.status_code == 200
    assert r.json()["model"] == "primary"


async def test_mismatch_updates_metrics():
    with patch("app.services.llm_client.call_primary", new_callable=AsyncMock) as mock_primary, \
         patch("app.services.llm_client.call_candidate", new_callable=AsyncMock) as mock_candidate:
        mock_primary.return_value = {"model": "primary", "output": "Paris"}
        mock_candidate.return_value = {"model": "candidate", "output": "Lyon"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            await client.post("/proxy", json={"prompt": "test"})

    assert metrics.mismatches == 1
    assert metrics.matches == 0


async def test_metrics_match_rate():
    with patch("app.services.llm_client.call_primary", new_callable=AsyncMock) as mock_primary, \
         patch("app.services.llm_client.call_candidate", new_callable=AsyncMock) as mock_candidate:
        mock_primary.return_value = {"model": "primary", "output": "Paris"}
        mock_candidate.return_value = {"model": "candidate", "output": "Paris"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            for _ in range(3):
                await client.post("/proxy", json={"prompt": "test"})

            mock_candidate.return_value = {"model": "candidate", "output": "Lyon"}
            await client.post("/proxy", json={"prompt": "test"})

            r = await client.get("/metrics")

    data = r.json()
    assert data["total_shadow_requests"] == 4
    assert data["matches"] == 3
    assert data["mismatches"] == 1
    assert data["match_rate"] == 75.0
