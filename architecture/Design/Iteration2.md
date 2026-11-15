# Qaway — Iteration 2

Following the ADD method. As-built documentation of the second iteration.

## Iteration Goal
**Design the data-access layer that finds and downloads NISAR data from ASF.**

## Drivers to Address
- CON-1: Use NISAR data
- CON-4: Acquire via ASF with the Earthdata token
- QA-6: Interoperability

## ADD Process Steps

### Step 2: Establish goal by selecting drivers
A module that, given an area, searches and downloads the right NISAR products, grouped by
comparable geometry, using the existing Earthdata token (CON-1, CON-4, QA-6).

### Step 3: Choose elements to refine
Refine the **Data-access module** (`mcp_server/asf_client.py`) between the Backend and ASF.

### Step 4: Choose design concepts
| Selected design concept | Rationale | Discarded alternatives |
|---|---|---|
| **`asf_search` library (ASF/CMR)** | Official, authenticated NISAR search+download (CON-4, QA-6) | Raw CMR REST (reinvent, brittle) |
| **Group scenes by geometry (track + direction)** | Change detection requires comparable passes | Flat scene list (user would mix geometries) |
| **Token in gitignored secrets file (perms 600)** | Keep credentials out of code/repo | Hard-coded token (leak risk) |
| **Product selection: GCOV (change/flood) + GUNW (deformation/coherence)** | Matches the hazards Qaway detects | SLC/raw (needs full InSAR processing) |

### Step 5: Instantiate elements
| Instantiation decision | Rationale |
|---|---|
| `search_by_bbox(bbox, processing_level)` | Search NISAR over a polygon, by product |
| `_group_by_geometry()` | Return passes grouped by track/direction |
| `download_granules(granulos)` | Download selected scenes; skips files already present |
| Data saved to `sarvigia/data/` (volume) | Local cache shared with processing |

### Step 6: Record design decisions
| Driver | Decision | Rationale | Discarded alternatives |
|---|---|---|---|
| CON-1/CON-4 | `asf_search` + Earthdata token | Official NISAR access | Custom HTTP to CMR |
| QA-6 | Group by geometry; select GCOV+GUNW | Interoperable, analysis-ready | Return all products ungrouped |
| Security | Token in `config/secrets.yaml` (600, gitignored) | No credential leak | Token in source |

> Note: the folder is named `mcp_server/` from an early MCP prototype but is used as a plain
> Python module — Qaway does not run the MCP protocol.

### Step 7: Analysis
| Driver | Analysis result |
|---|---|
| CON-1 | **Satisfied** — NISAR GCOV & GUNW are the primary data. |
| CON-4 | **Satisfied** — acquired via ASF with the Earthdata token. |
| QA-6 | **Satisfied** — scenes grouped by geometry; analysis-ready products selected. |
