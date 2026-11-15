# Qaway — Iteration 6

Following the ADD method. As-built documentation of the sixth iteration.

## Iteration Goal
**Realize modifiability: add the multi-hazard analysis modules (deformation, coherence/fusion,
flood, terrain) without changing the core.**

## Drivers to Address
- SV-4: Detect landslide (occurred)
- SV-5: Early warning (slow movement)
- SV-6: Detect river flooding
- QA-4: Modifiability (add a new hazard without touching the core)

## ADD Process Steps

### Step 2: Establish goal by selecting drivers
Each hazard is an independent analysis module plus one agent tool, so adding a hazard touches only
new files — proving the modifiability driver (QA-4).

### Step 3: Choose elements to refine
Refine the **Processing** package (`processing/`) by adding one module per hazard, and the **Agent**
by adding one tool per module.

### Step 4: Choose design concepts
| Selected design concept | Rationale | Discarded alternatives |
|---|---|---|
| **One module per hazard (plug-in style)** | Add a hazard = add a file + a tool (QA-4) | Monolithic analysis function |
| **Certified / official methods per hazard** | Reproducible, defensible to a science jury | Ad-hoc thresholds only |
| **Fusion (intensity + coherence)** | Confirm a hazard with two independent signals → fewer false alarms | Single-signal detection |
| **Terrain context (DEM slope)** | Explains *why* a zone is susceptible | Change-only, no context |

### Step 5: Instantiate elements
| Module | Method | Driver |
|---|---|---|
| `backscatter_cd.py` | Log-ratio dB + Wishart/Conradsen (α) | SV-4 |
| `deformacion.py` | InSAR phase → LOS mm, −(λ/4π)·φ (GUNW) | SV-5 |
| `coherence_cd.py` | Coherence threshold + fusion with intensity | SV-4/5 |
| `inundacion.py` | Otsu water threshold + change (NASA ARSET) | SV-6 |
| `terreno.py` | DEM slope gradient (Copernicus GLO-30) | SV-5 |
| Agent tools (one per module) | `analizar_cambios_nisar`, `medir_deformacion`, `confirmar_con_coherencia`, `detectar_inundacion`, `evaluar_terreno` | QA-4 |

### Step 6: Record design decisions
| Driver | Decision | Rationale | Discarded alternatives |
|---|---|---|---|
| QA-4 | Plug-in module + tool per hazard | Flood was added this way with no core change | Monolithic analysis |
| SV-4 | Log-ratio (ASF) + Wishart statistical test | Official + α-controlled significance | Fixed dB threshold only |
| SV-5 | InSAR displacement from GUNW | NASA landslide white-paper method | None (core early-warning value) |
| SV-6 | Otsu + change (ARSET) | NASA-backed flood mapping | Hand-tuned threshold |
| Confidence | Fuse intensity + coherence | Two independent signals → fewer false alarms | Single signal |

### Step 7: Analysis
| Driver | Analysis result |
|---|---|
| SV-4 | **Satisfied** — change detection flags occurred landslides. |
| SV-5 | **Partially satisfied** — single-pair InSAR gives an *indicative* early warning; a time series (dolphin/SBAS) would confirm. |
| SV-6 | **Satisfied** — flood module detects new water / overflow (reliable on open water / rivers; harder in dense cities). |
| QA-4 | **Satisfied** — adding floods required only a new module + tool, proving modifiability. |
