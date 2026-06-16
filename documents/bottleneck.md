# System Bottlenecks

## Bottleneck 1 — In-process BackgroundTasks (highest risk)

**Problem:** `background_tasks.add_task()` runs inside the same server process. If the server restarts or crashes mid-shadow, the task is lost silently. Under high traffic, a backlog of shadow tasks competes with the primary response path for the same event loop.

**Fix:** Replace with `asyncio.Queue` + dedicated worker, then Celery/RQ for multi-process scale.

---

## Bottleneck 2 — In-memory metrics

**Problem:** Counters live in a Python object. Server restart = all metrics gone. Cannot query history, cannot aggregate across multiple server instances.

**Fix:** Redis for live counters, PostgreSQL for historical records.

---

## Bottleneck 3 — Primary LLM is a single synchronous call

**Problem:** Every `/proxy` request blocks waiting for the Primary response. If the Primary LLM is slow or degraded, all users wait. No timeout, no retry, no circuit breaker.

**Fix:** Add timeout to `call_primary`, circuit breaker to stop hammering a degraded Primary, and retry with backoff for transient failures.

---

## Bottleneck 4 — No Candidate timeout enforcement at scale

**Problem:** `CANDIDATE_TIMEOUT_SECONDS` exists in config but under a shadow task backlog, many timed-out candidates pile up in the event loop.

**Fix:** The queue/worker architecture from Bottleneck 1 naturally solves this — workers process one task at a time with controlled concurrency.

---

## Priority

| Bottleneck | Phase |
|---|---|
| In-process BackgroundTasks → queue/worker | Phase 3 |
| In-memory metrics → Redis + PostgreSQL | Phase 3 |
| Primary timeout + circuit breaker | Phase 3 |
| Candidate timeout at scale | Phase 3 (resolved by queue/worker) |
