# Shadow LLM Evaluator

A FastAPI proxy that serves customer traffic using a Primary LLM, while asynchronously shadowing requests to a Candidate LLM and logging mismatches. Built to safely evaluate a new model without affecting customer-facing latency or reliability.

---

## Architecture

```
https://app.excalidraw.com/l/8rzXlKtSNFV/70Lh348gyyn
```

The user only waits for the Primary call. Everything else happens after the response is already sent.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/proxy` | Main customer endpoint |
| `GET` | `/health` | Liveness check |
| `GET` | `/metrics` | Match/mismatch stats |
| `POST` | `/mock/primary` | Simulated Primary LLM |
| `POST` | `/mock/candidate` | Simulated Candidate LLM (supports `?delay_ms=`) |

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/doudoudope/sarah-shadow-llm-evaluator
cd sarah-shadow-llm-evaluator
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Copy environment config**
```bash
cp .env.example .env
```

**4. Start Redis**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

**5. Start the server**
```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

---

## Configuration

All config is set via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `PRIMARY_LLM_URL` | `http://localhost:8000/mock/primary` | Primary LLM endpoint |
| `CANDIDATE_LLM_URL` | `http://localhost:8000/mock/candidate` | Candidate LLM endpoint |
| `PRIMARY_TIMEOUT_SECONDS` | `5` | Timeout for Primary call |
| `CANDIDATE_TIMEOUT_SECONDS` | `10` | Timeout for Candidate call |
| `SHADOW_QUEUE_MAXSIZE` | `1000` | Max shadow tasks in queue |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Demo

**Health check**
```bash
curl http://localhost:8000/health
```

**Send a prompt**
```bash
curl -X POST http://localhost:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

**Check metrics**
```bash
curl http://localhost:8000/metrics
```

**Prove Redis persistence** — restart the server and check metrics again, counts are preserved:
```bash
# Ctrl+C to stop server
uvicorn app.main:app --reload
curl http://localhost:8000/metrics
```

**Prove latency isolation** — proxy returns instantly even when candidate is slow:
```bash
# In one terminal, make candidate slow
curl -X POST "http://localhost:8000/mock/candidate?delay_ms=3000" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Proxy still returns immediately
curl -X POST http://localhost:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

---

## Testing

Run the full test suite (no server or Redis needed):

```bash
pytest tests/ -v
```

Run only unit tests:
```bash
pytest tests/unit/ -v
```

Run only integration tests:
```bash
pytest tests/integration/ -v
```

**What is tested:**

Unit tests (`tests/unit/`):
- JSON extraction from clean JSON
- JSON extraction from text containing JSON
- JSON extraction failure returns `None`
- Matching JSON comparison
- Mismatching JSON comparison

Integration tests (`tests/integration/`):
- `/proxy` returns Primary response
- Slow Candidate does not delay `/proxy`
- Candidate failure does not fail `/proxy`
- Mismatch increments metrics correctly
- `/metrics` returns correct match rate

Tests use `fakeredis` — no real Redis instance required to run tests.

---

## Production Testing

Live app: `https://sarah-app-pab55.ondigitalocean.app`

**Health check**
```bash
curl https://sarah-app-pab55.ondigitalocean.app/health
```

**Send a prompt**
```bash
curl -X POST https://sarah-app-pab55.ondigitalocean.app/proxy \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

**Check metrics**
```bash
curl https://sarah-app-pab55.ondigitalocean.app/metrics
```

**Trigger a mismatch** — candidate mock returns a different answer:
```bash
for i in 1 2 3; do
  curl -s -X POST https://sarah-app-pab55.ondigitalocean.app/proxy \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test"}' | jq .
done
curl https://sarah-app-pab55.ondigitalocean.app/metrics
```

**Prove latency isolation** — proxy returns fast even with slow candidate:
```bash
time curl -X POST "https://sarah-app-pab55.ondigitalocean.app/mock/candidate?delay_ms=3000" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

time curl -X POST https://sarah-app-pab55.ondigitalocean.app/proxy \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

---

## Production Improvements (Phase 3)

| Improvement | Why |
|---|---|
| Celery / RQ task queue | Shadow tasks survive process restarts |
| PostgreSQL for mismatch history | Queryable permanent record of all shadow results |
| Retry + circuit breaker on Primary | Handles transient failures gracefully |
| Prometheus metrics | Dashboarding and alerting |
| Structured JSON logging | Machine-parseable logs for aggregators |
| Auth + rate limiting | Production readiness |
