# Qaway — Iteration 5

Following the ADD method. As-built documentation of the fifth iteration.

## Iteration Goal
**Design the agentic AI voice assistant (the core differentiator).**

## Drivers to Address
- SV-1: Ask by voice (natural language)
- SV-7: Two depth levels, two languages
- SV-8: Risk read-out & physical reasoning
- QA-5: Reliability (agent)
- CRN-5: AI layer must not destabilize the core pipeline

## ADD Process Steps

### Step 2: Establish goal by selecting drivers
A brain that understands any question (any phrasing, ES/EN), **decides which analysis to run**,
reads the real numbers, and answers by voice — simple or technical — reliably, without coupling to
the core pipeline.

### Step 3: Choose elements to refine
Introduce the **AI Agent** component (`backend/agent.py`) between the API and the LLM.

### Step 4: Choose design concepts
| Selected design concept | Rationale | Discarded alternatives |
|---|---|---|
| **Agentic LLM with tool-calling** | LLM decides intent and which analysis to run — not a fixed menu (SV-1) | Rule-based intent parser (brittle, template-like) |
| **Local LLM (Ollama / Qwen2.5)** | Free, private, reuses the team GPU (CON-7) | Cloud LLM API (cost, key, data leaves PC) |
| **Tools = thin wrappers over processing results** | One tool per capability; agent composes them (SV-8) | LLM invents numbers (hallucination) |
| **Severity computed in code, not by the LLM** | Deterministic, trustworthy | LLM estimates severity (unreliable) |
| **Auto-retry on garbled tool calls** | Local 7B model occasionally leaks malformed calls (QA-5) | Trust single call (~50% failures observed) |

### Step 5: Instantiate elements
| Instantiation decision | Rationale |
|---|---|
| `POST /api/preguntar {pregunta, idioma, nivel, contexto}` | Single agent entry point |
| Agent tools: cambios, deformación, coherencia/fusión, terreno, inundación, ubicación, analizar_mi_zona | One tool per capability |
| Direct-narration mode when stats are provided | Deterministic result narration |
| ES/EN + simple/technical in the system prompt | Serves each audience |
| Ollama reached via Docker `host.docker.internal` | Container → host LLM |

### Step 6: Record design decisions
| Driver | Decision | Rationale | Discarded alternatives |
|---|---|---|---|
| SV-1 | Agentic LLM + tool-calling | Any phrasing/language; reasons and acts | Fixed-keyword router |
| CON-7, privacy | Ollama/Qwen2.5 local | No cost/key; data on the PC | Cloud API |
| SV-8 | Tools return real stats; severity in code | Grounded, no hallucination | LLM free-form numbers |
| QA-5 | Auto-retry on garbled output | Robust against flaky 7B tool-calls | Single attempt |
| CRN-5 | Agent is an add-on over the pipeline | Core stays stable | Agent embedded in core |

### Step 7: Analysis
| Driver | Analysis result |
|---|---|
| SV-1 | **Satisfied** — any natural-language question is understood and answered by voice. |
| SV-7 | **Satisfied** — ES/EN and simple/technical driven by toggles. |
| SV-8 | **Satisfied** — answers grounded in real stats + slope; severity computed in code. |
| QA-5 | **Satisfied** — auto-retry recovers from garbled tool calls (~50% → reliable). |
| CRN-5 | **Satisfied** — agent sits beside the pipeline; does not destabilize it. |
