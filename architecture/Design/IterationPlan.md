# Qaway — Iteration Plan

ADD iterations for **Qaway**, the open-source web app that turns NISAR radar into **spoken,
actionable road-hazard alerts** (NASA Space Apps 2026 — *Dancing with the SARs*). The plan is
**as-built**: it reflects the iterations actually implemented in `spaceapps/sarvigia/`.
Status: ✅ done · ⚠️ partial · 🔮 future.

## Iteration Plan Overview

| Iteration | Goal | Drivers | Status |
|---|---|---|---|
| 1 | Establish system structure & deployment | CRN-1, CON-2, CON-3, QA-7 | ✅ |
| 2 | Data-access layer (search & download NISAR from ASF) | CON-1, CON-4, QA-6 | ✅ |
| 3 | Processing pipeline — async jobs + caching | SV-3, QA-1, QA-2, QA-8, CRN-3 | ✅ |
| 4 | Frontend & the two usage modes (voice / polygon + GPS corridor) | SV-1, SV-2, QA-3 | ✅ |
| 5 | Agentic AI voice assistant (Ollama/Qwen2.5) + ES/EN + levels | SV-1, SV-7, SV-8, QA-5, CRN-5 | ✅ |
| 6 | Multi-hazard modules — modifiability realized | SV-4, SV-5, SV-6, QA-4 | ✅ |

## Detailed Iteration Goals

### Iteration 1 — System structure & deployment ✅
Reference architecture and deployment: web frontend (nginx), REST backend (FastAPI), data-access
module, local processing, and the LLM. Deployed reproducibly on the author's single self-hosted
server with **Docker + Cloudflare Tunnel**, open-source (CRN-1, CON-2, CON-3, QA-7).

### Iteration 2 — Data-access layer ✅
Component that finds and acquires NISAR data for an area from **ASF**, authenticated with the
Earthdata token (`asf_search`). Returns scenes grouped by comparable geometry (track/direction)
and auto-selects the products: **GCOV** (change / flood) and **GUNW** (deformation / coherence).
(`mcp_server/asf_client.py` — folder name historical; used as a plain Python module, not MCP.)

### Iteration 3 — Processing pipeline: async jobs + caching ✅
Raw scenes → analysis products **off the request path** (CRN-3). A new-area request (SV-3) creates
an async job acknowledged immediately (QA-2); the backend downloads the latest pair + GUNW, crops
**only the polygon window** (→ ~1–2 s, QA-1) and runs the analyses. Downloaded scenes are cached
and bounded by an **LRU cleanup (100 GB cap, demo pinned)** so they are reused, never re-downloaded
(QA-8). `backend/app.py`, `backend/limpieza.py`.

### Iteration 4 — Frontend & the two usage modes ✅
Interactive **MapLibre** map with **two ways to use it**: (A) **voice** — the driver asks and the
app takes GPS and draws a **road corridor** (Overpass + Turf.js); (B) **draw a polygon** — an analyst
marks an exact area (SV-1, SV-2). Auto-picks the 2 latest passes; clean, mobile-first UI (QA-3).

### Iteration 5 — Agentic AI voice assistant ✅
The core differentiator: an **agentic LLM** (Ollama/**Qwen2.5**, local GPU) with **tool-calling**
that understands any phrasing, **decides which analysis to run**, reads the real numbers and
**answers by voice** — in **Spanish/English**, **simple/technical** (SV-1, SV-7, SV-8). Robustness:
auto-retry on garbled tool calls (QA-5). The agent is an add-on that does not destabilize the core
pipeline (CRN-5). `backend/agent.py`.

### Iteration 6 — Multi-hazard modules (modifiability) ✅
Extension realized: each hazard is an independent `processing/*.py` module + one agent tool, added
without touching the core (QA-4):
- `backscatter_cd.py` — landslide / change (log-ratio + Wishart).
- `deformacion.py` — slow movement / early warning (InSAR mm).
- `coherence_cd.py` — coherence + fusion (confidence).
- `inundacion.py` — river flooding (Otsu + change, NASA ARSET).
- `terreno.py` — slope / susceptibility (Copernicus DEM).
Adding floods as a new module+tool proved the modifiability driver in practice.

## Not implemented (future work) 🔮
- **Offline-first alerting** (pre-cache route + on-device alert without signal).
- **Durable jobs** (Redis/Postgres) — jobs are in memory (lost on restart).
- **Time-series deformation** (JPL dolphin / SBAS, GPU) — current deformation is a single pair (indicative).
- **Time-series animation, before/after swipe, export/share, zone management, observability dashboard.**
- **Remote-subset download** (crop on acquire) — would cut download from GB to MB.

## Notes
- Hackathon-oriented: each iteration is independently demonstrable to reduce risk (CRN-5).
- Team **thecreator**: Lino Ever Ramos Maíz · Silvana Rossío Pacheco Malpartida.
