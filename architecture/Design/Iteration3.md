# Qaway — Iteration 3

Following the ADD method. As-built documentation of the third iteration.

## Iteration Goal
**Design the processing pipeline with asynchronous jobs and caching.**

## Drivers to Address
- SV-3: Analyze a new area
- QA-1: Performance (processing)
- QA-2: Responsiveness
- QA-8: Efficiency / caching
- CRN-3: Keep heavy processing off the request path

## ADD Process Steps

### Step 2: Establish goal by selecting drivers
Turn raw NISAR scenes into hazard products without blocking the user: an async job per request,
fast because it processes only the drawn area, with caching so nothing is re-downloaded.

### Step 3: Choose elements to refine
Refine the **Backend orchestrator** (`app.py`) and introduce the **Processing** modules and the
**cache-cleanup** component.

### Step 4: Choose design concepts
| Selected design concept | Rationale | Discarded alternatives |
|---|---|---|
| **Asynchronous job + polling** (`/analisis` → `/jobs/{id}`) | Request returns instantly; heavy work in a thread (QA-2, CRN-3) | Synchronous processing (UI blocks minutes) |
| **Crop-only window from HDF5** | Read MBs not GBs → ~1–2 s per area (QA-1) | Process the full 330 km scene (slow, heavy) |
| **Download semaphore (1 at a time)** | Avoid saturating the PC/network | Unbounded parallel downloads |
| **LRU disk cache with cap + pinned demo** | Reuse scenes; bound disk (QA-8) | Keep all (disk fills) / delete all (re-download) |

### Step 5: Instantiate elements
| Instantiation decision | Rationale |
|---|---|
| `POST /api/analisis` → thread `_run_job` | Async job, returns `job_id` |
| `GET /api/jobs/{id}` | Progress / result polling |
| `processing/backscatter_cd.py` (first module) | Change detection on the GCOV pair |
| `backend/limpieza.py` (LRU, 100 GB, pin demo) | Bounded cache |
| Window read via coordinate indices (pyproj) | Crop to the polygon only |

(See Sequence Diagrams SEQ-1/SEQ-2 in `Architecture.md`.)

### Step 6: Record design decisions
| Driver | Decision | Rationale | Discarded alternatives |
|---|---|---|---|
| QA-2, CRN-3 | Async job + polling | Instant ack; heavy work off request path | Synchronous call |
| QA-1 | Crop only the bbox window | ~1–2 s even for ~5 km areas | Full-scene processing |
| QA-8 | LRU cleanup 100 GB, pin demo | Reuse + bounded disk | Keep-all / delete-all |

### Step 7: Analysis
| Driver | Analysis result |
|---|---|
| SV-3 | **Satisfied** — any new area creates a job that downloads + processes it. |
| QA-1 | **Satisfied** — ~1–2 s processing (crop window). |
| QA-2 | **Satisfied** — request returns a `job_id` immediately. |
| QA-8 | **Satisfied** — LRU cache (100 GB) reuses scenes, pins the demo. |
| CRN-3 | **Satisfied** — processing runs in a background thread, not on the request path. |
