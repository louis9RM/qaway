# Qaway — Iteration 1

Following the Attribute-Driven Design (ADD) method. As-built documentation of the first iteration.

## Iteration Goal
**Establish the overall system structure and deployment model.**

## Drivers to Address
- CRN-1: Establish an overall initial system structure
- CON-2: Open-source
- CON-3: Self-hosted on a single server
- QA-7: Deployability

## ADD Process Steps

### Step 2: Establish goal by selecting drivers
Define the reference architecture and a reproducible, open-source deployment on the author's
single self-hosted server (CRN-1, CON-2, CON-3, QA-7).

### Step 3: Choose elements to refine
Greenfield → the element to refine is the **whole system**: its high-level structure
(frontend, backend, data, processing, LLM) and its deployment model.

### Step 4: Choose design concepts
| Selected design concept | Rationale | Discarded alternatives |
|---|---|---|
| **Client–server + REST API** | Clear split web UI ↔ backend; simple, well-understood | Monolith UI+logic (hard to evolve) |
| **Containerized deployment (Docker Compose)** | Reproducible on one PC; isolates frontend/backend (QA-7, CON-3) | Bare-metal install (fragile, non-reproducible) |
| **Reverse proxy + Cloudflare Tunnel** | Public HTTPS URL from a self-hosted PC with no fixed IP | Direct port exposure (insecure, no TLS) |
| **Local-first stack (Python + JS)** | Leverages author's strengths; no paid cloud (CON-2/3) | Managed cloud PaaS (cost, lock-in) |

### Step 5: Instantiate elements
| Instantiation decision | Rationale |
|---|---|
| `frontend` container (nginx static) at :8101 | Serves the web app, isolated |
| `backend` container (FastAPI/uvicorn) at :8100 | API + orchestration |
| Cloudflare Tunnel → `qaway.thecreatorcampus.ai` | Public demo URL for judges |
| `deploy/docker-compose.yml` | One-command reproducible deploy |

(See the Container Diagram in `Architecture.md`.)

### Step 6: Record design decisions
| Driver | Decision | Rationale | Discarded alternatives |
|---|---|---|---|
| CON-3, QA-7 | Docker Compose (frontend + backend) on the PC | Reproducible, isolated, one command | VM / bare metal |
| CRN-1 | Client–server with REST `/api` | Simple, decoupled skeleton | Monolith |
| Public access | Cloudflare Tunnel | HTTPS from self-host without fixed IP | ngrok (ephemeral) / open ports |

### Step 7: Analysis
| Driver | Analysis result |
|---|---|
| CRN-1 | **Satisfied** — skeleton (frontend/backend/data/processing/LLM) defined. |
| CON-2 | **Satisfied** — fully open-source stack. |
| CON-3 | **Satisfied** — runs on the author's single server. |
| QA-7 | **Satisfied** — `docker compose up -d` redeploys reproducibly; Cloudflare serves the public URL. |
