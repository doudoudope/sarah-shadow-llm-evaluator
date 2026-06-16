# Shadow LLM Evaluator — MVP Design

## Decisions

- `/mock/candidate` accepts optional `?delay_ms=` query param for latency simulation
- Comparison: equal JSON object = match, anything else = mismatch (no field-level diff)
- Log destination: stdout (structured JSON lines)

---

## Architecture Flow

```
Client
  │
  ▼
POST /proxy
  │
  ├─── [SYNC] → httpx POST /mock/primary
  │               └─ Primary response (fast)
  │
  ├─── return Primary response to Client ◄── customer sees this immediately
  │
  └─── [BACKGROUND TASK enqueued with FastAPI BackgroundTasks]
         │
         ▼
       httpx POST /mock/candidate  (timeout = CANDIDATE_TIMEOUT_SECONDS)
         │
         ├── on success → extract_json(candidate_output)
         │                extract_json(primary_output)
         │                compare()
         │                → log result
         │                → update MetricsStore
         │
         └── on failure/timeout → log error, increment mismatch, continue
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/proxy` | Main customer endpoint |
| `POST` | `/mock/primary` | Primary LLM mock |
| `POST` | `/mock/candidate` | Candidate LLM mock (supports `?delay_ms=`) |
| `GET` | `/metrics` | In-memory match/mismatch stats |
| `GET` | `/health` | Liveness probe |

**Request** (`/proxy`, `/mock/*`):
```json
{ "prompt": "string" }
```

**Response** (`/proxy`, `/mock/*`):
```json
{ "model": "primary", "output": "Paris" }
```

**Metrics response**:
```json
{ "total_shadow_requests": 100, "matches": 92, "mismatches": 8, "match_rate": 92.0 }
```

---

## Project Structure

```
sarah-shadow-llm-evaluator/
├── app/
│   ├── main.py              # FastAPI app, router registration
│   ├── config.py            # Env var config (pydantic Settings)
│   ├── metrics.py           # In-memory MetricsStore singleton
│   ├── logging_config.py    # Logger setup
│   ├── routers/
│   │   ├── proxy.py         # POST /proxy
│   │   ├── mock.py          # POST /mock/primary, /mock/candidate
│   │   └── metrics.py       # GET /metrics, GET /health
│   ├── services/
│   │   ├── llm_client.py    # httpx async calls to Primary/Candidate
│   │   └── shadow.py        # Background shadow task orchestration
│   └── utils/
│       ├── json_extract.py  # Extract JSON from messy strings
│       └── comparison.py    # Compare extracted JSON objects
├── tests/
│   ├── unit/
│   │   ├── test_json_extract.py
│   │   └── test_comparison.py
│   └── integration/
│       └── test_proxy.py
├── .env.example
├── requirements.txt
└── CLAUDE.md
```

---

## Key Data Structures

**MetricsStore** (singleton, module-level, protected by `asyncio.Lock`):
```
total_shadow_requests: int
matches: int
mismatches: int
```

**Mismatch log entry** (written to stdout as structured JSON):
```
request_id: str        # uuid4
prompt: str
primary_output: str
candidate_output: str
extracted_primary_json: dict | None
extracted_candidate_json: dict | None
matched: bool
error: str | None
timestamp: str         # ISO8601
```

---

## Milestones

### Milestone 1 — Project Skeleton (~25 min)
**Goal:** Runnable app with all routes stubbed, config wired, health check live.

1. Create directory structure (`app/`, `app/routers/`, `app/services/`, `app/utils/`, `tests/unit/`, `tests/integration/`)
2. `requirements.txt` — `fastapi`, `uvicorn`, `httpx`, `pytest`, `pytest-asyncio`
3. `app/config.py` — pydantic `Settings` reading: `PRIMARY_LLM_URL`, `CANDIDATE_LLM_URL`, `CANDIDATE_TIMEOUT_SECONDS`, `LOG_LEVEL`
4. `.env.example` with defaults pointing to `http://localhost:8000/mock/primary` etc.
5. `app/main.py` — FastAPI app, router registration, startup log
6. `GET /health` returns `{"status": "healthy"}`

**Done when:** `uvicorn app.main:app` starts; `curl /health` returns 200.

---

### Milestone 2 — Mock Endpoints (~20 min)
**Goal:** Both LLM mocks return realistic responses. Candidate supports artificial delay.

1. `app/routers/mock.py`
2. `POST /mock/primary` — accepts `{"prompt": str}`, returns `{"model": "primary", "output": "Paris"}`
3. `POST /mock/candidate` — accepts `{"prompt": str}` + optional `?delay_ms=int`, sleeps async, returns `{"model": "candidate", "output": "Paris"}`
4. Register router in `main.py`

**Done when:** Both mock routes return expected JSON; Candidate with `?delay_ms=2000` actually waits ~2 seconds.

---

### Milestone 3 — Proxy Synchronous Path (~25 min)
**Goal:** `/proxy` calls Primary synchronously and returns the response. No shadow yet.

1. `app/services/llm_client.py` — async `call_primary(prompt)` using `httpx.AsyncClient`
2. `app/routers/proxy.py` — `POST /proxy`, validates input, calls `call_primary`, returns Primary response
3. Primary failure (non-2xx or connection error) → return `502`

**Done when:** `POST /proxy {"prompt": "..."}` returns Primary response; killing the mock returns 502.

---

### Milestone 4 — JSON Utilities + Unit Tests (~30 min)
**Goal:** Pure utility functions for extraction and comparison, fully unit-testable with no I/O.

1. `app/utils/json_extract.py` — `extract_json(text: str) -> dict | None`
   - Try `json.loads(text)` first
   - Fall back to regex scan for first `{...}` substring
   - Return `None` on failure
2. `app/utils/comparison.py` — `compare(a: dict | None, b: dict | None) -> bool`
   - Returns `True` only if both non-None and `a == b`
3. Unit tests:
   - Extract from clean JSON string
   - Extract from text containing JSON
   - Extract from text with no JSON → `None`
   - Matching dicts → `True`
   - Different dicts → `False`
   - One or both `None` → `False`

**Done when:** `pytest tests/unit/` all green.

---

### Milestone 5 — Shadow Execution + Mismatch Logging (~35 min)
**Goal:** Background task calls Candidate, compares, logs. Primary path unaffected.

1. `app/services/llm_client.py` — add `call_candidate(prompt)` with `CANDIDATE_TIMEOUT_SECONDS` timeout
2. `app/metrics.py` — `MetricsStore` singleton with `asyncio.Lock`
3. `app/logging_config.py` — configure Python logger, JSON-formatted output
4. `app/services/shadow.py` — `async def run_shadow(request_id, prompt, primary_output)`:
   - Entirely wrapped in `try/except`
   - Calls `call_candidate`
   - Extracts JSON from both outputs
   - Compares and logs structured result
   - Updates `MetricsStore`
5. `app/routers/proxy.py` — enqueue `run_shadow` via `BackgroundTasks` after returning Primary response

**Done when:** Logs show shadow task executed after response returned; Candidate errors logged without affecting proxy response.

---

### Milestone 6 — Metrics Endpoint (~15 min)
**Goal:** `/metrics` reflects real shadow execution counts.

1. `app/routers/metrics.py` — `GET /metrics` reads from `MetricsStore`, computes `match_rate` (0.0 if total=0)

**Done when:** After several `/proxy` calls, `/metrics` shows correct totals and rate.

---

### Milestone 7 — Integration Tests (~30 min)
**Goal:** Automated tests prove all key behaviors.

| Test | Assertion |
|---|---|
| `/proxy` returns Primary response | status 200, `model == "primary"` |
| `/proxy` is fast when Candidate is slow | response time < 500ms with `delay_ms=3000` Candidate |
| Candidate failure does not fail `/proxy` | status 200 even when Candidate URL is unreachable |
| Mismatch increments metrics | `/metrics` mismatch count increases after differing outputs |
| `/metrics` match rate correct | after N calls, `match_rate` = matches/total × 100 |

**Done when:** `pytest tests/` all green.

---

## Definition of MVP Done

- `pytest tests/` all green, including the latency isolation test
- `POST /proxy` with a slow Candidate returns in Primary time
- `GET /metrics` reflects accurate counts after shadow runs
- All mismatch logs visible in stdout with `request_id`, `prompt`, both outputs, and timestamp

---

## Non-MVP (Phase 2 and Beyond)

| Feature | Phase |
|---|---|
| README + architecture diagram | Phase 2 |
| GitHub Actions CI | Phase 2 |
| Dockerfile + docker-compose | Phase 2 |
| Async task queue (ARQ/Celery) | Phase 3 |
| PostgreSQL for mismatch history | Phase 3 |
| Prometheus metrics | Phase 3 |
| Structured JSON logging | Phase 3 |
| Candidate retry with backoff | Phase 3 |
| Circuit breaker | Phase 3 |
| Auth + rate limiting | Phase 3 |
