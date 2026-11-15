# Qaway — Iteration 4

Following the ADD method. As-built documentation of the fourth iteration.

## Iteration Goal
**Design the frontend and the two usage modes (voice and draw-polygon, with GPS corridor).**

## Drivers to Address
- SV-1: Ask by voice
- SV-2: Draw a polygon
- QA-3: Usability

## ADD Process Steps

### Step 2: Establish goal by selecting drivers
A mobile-first web map that a driver can use **by voice** (hands-free) and an analyst can use by
**drawing a polygon**, both understandable by non-experts (QA-3).

### Step 3: Choose elements to refine
Refine the **Frontend** (`index.html`, `js/app.js`, `js/config.js`) and its interaction with the API.

### Step 4: Choose design concepts
| Selected design concept | Rationale | Discarded alternatives |
|---|---|---|
| **MapLibre GL (web map)** | Open-source interactive map; mobile-first | Static image / paid map SDK |
| **PWA-style web app** | No install; judges just open a link; one codebase | Native Android app (install friction, one OS) |
| **Voice mode (Web Speech API)** | Hands-free for a driver (SV-1) | Typing only (unsafe while driving) |
| **Road corridor (Overpass + Turf.js buffer)** | Analyze the road, not a blind square → less noise, less data | Fixed square around GPS (irrelevant hills) |
| **Auto-pick the 2 latest passes** | No manual date menu; always current (SV-3) | Manual date dropdowns (friction) |

### Step 5: Instantiate elements
| Instantiation decision | Rationale |
|---|---|
| Draw-polygon tool + GPS "use my location" | Two input modes (SV-1/SV-2) |
| `analizarCorredor()` (Overpass + Turf buffer) | Road-following corridor |
| ES/EN + simple/technical toggles | One result served to several audiences |
| Clean, mobile-first UI (no clutter) | Usability (QA-3) |

### Step 6: Record design decisions
| Driver | Decision | Rationale | Discarded alternatives |
|---|---|---|---|
| SV-1/SV-2 | Two modes: voice + draw polygon | Driver and analyst use cases | Single mode |
| Relevance | Road corridor (buffer of OSM road) | Analyze only the road + adjacent slopes | Blind square (noise, extra data) |
| QA-3 | Mobile-first, minimal UI, auto dates | Non-expert understands fast | Dense analyst dashboard |

### Step 7: Analysis
| Driver | Analysis result |
|---|---|
| SV-1 | **Satisfied** — voice mode drives the whole flow hands-free. |
| SV-2 | **Satisfied** — draw-polygon analyzes an exact area. |
| QA-3 | **Satisfied** — clean mobile-first UI; non-experts interpret results quickly. |
