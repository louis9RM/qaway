"""Qaway — Módulo de coherencia (NISAR GUNW) + FUSIÓN con el cambio de intensidad.

La coherencia interferométrica mide cuán "igual" ve el radar un punto entre dos fechas:
  - coherencia ALTA  → superficie estable (no se movió)
  - coherencia BAJA  → superficie perturbada (removida, deslizada, mojada)

FUSIÓN (máxima precisión, respaldada por la literatura): se confirma deslizamiento donde
el CAMBIO DE INTENSIDAD (Wishart, backscatter_cd) **y** la CAÍDA DE COHERENCIA coinciden
→ menos falsas alarmas, más confianza.

Producto: NISAR L2 GUNW, capa `coherenceMagnitude` (0..1).
"""
from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

COH_GRID = "science/LSAR/GUNW/grids/frequencyA/wrappedInterferogram/HH"


def leer_coherencia(h5_path: str, bbox_lonlat):
    with h5py.File(h5_path, "r") as h5:
        g = h5[COH_GRID]
        x = g["xCoordinates"][:]
        y = g["yCoordinates"][:]
        epsg = int(np.array(g["projection"]).item())
        tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
        W, S, E, N = bbox_lonlat
        xs, ys = tr.transform([W, E, W, E], [S, S, N, N])
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        xi = np.where((x >= xmin) & (x <= xmax))[0]
        yi = np.where((y >= ymin) & (y <= ymax))[0]
        if xi.size == 0 or yi.size == 0:
            raise ValueError("El bbox no intersecta el GUNW.")
        x0, x1 = int(xi.min()), int(xi.max()) + 1
        y0, y1 = int(yi.min()), int(yi.max()) + 1
        coh = g["coherenceMagnitude"][y0:y1, x0:x1].astype(np.float32)
    coh = np.where(np.isfinite(coh) & (coh >= 0) & (coh <= 1), coh, np.nan)
    return coh


def resumen_coherencia(h5_path: str, bbox_lonlat, umbral_bajo: float = 0.3):
    coh = leer_coherencia(h5_path, bbox_lonlat)
    valid = np.isfinite(coh)
    if not valid.any():
        return {"error": "sin datos de coherencia"}
    c = coh[valid]
    n = c.size
    return {
        "coherencia_media": round(float(c.mean()), 3),
        "pct_baja_coherencia_<%.1f" % umbral_bajo: round(100.0 * np.count_nonzero(c < umbral_bajo) / n, 1),
        "umbral_bajo": umbral_bajo,
        "interpretacion": "coherencia baja = superficie perturbada (posible deslizamiento)",
        "fuente": "NISAR GUNW · coherenceMagnitude (banda L)",
    }


def fusionar(stats_cambio: dict, stats_coherencia: dict) -> dict:
    """Combina cambio de intensidad (Wishart) + coherencia → nivel de confianza."""
    pct_cambio = float(stats_cambio.get("pct_cambio", 0))
    coh_media = float(stats_coherencia.get("coherencia_media", 1))
    # claves con umbral dinámico en el nombre → tomar la primera que empiece por pct_baja
    pct_baja = next((v for k, v in stats_coherencia.items() if k.startswith("pct_baja")), 0)
    cambio_si = pct_cambio > 0.3
    coherencia_cayo = coh_media < 0.5 or float(pct_baja) > 30
    if cambio_si and coherencia_cayo:
        conf, verdict = "alta", "Deslizamiento MUY PROBABLE: el cambio de intensidad y la caída de coherencia coinciden."
    elif cambio_si or coherencia_cayo:
        conf, verdict = "media", "Cambio posible: solo una de las dos señales (intensidad o coherencia) es fuerte. Vigilar."
    else:
        conf, verdict = "baja", "Terreno estable: ni la intensidad ni la coherencia muestran perturbación significativa."
    return {
        "confianza": conf,
        "veredicto": verdict,
        "cambio_intensidad_pct": round(pct_cambio, 2),
        "coherencia_media": round(coh_media, 3),
        "pct_baja_coherencia": float(pct_baja),
        "metodo_fusion": "Intensidad (Wishart/ASF) + coherencia GUNW (banda L NISAR)",
    }


if __name__ == "__main__":
    DATA = Path(__file__).resolve().parents[1] / "data"
    GUNW = DATA / "NISAR_L2_PR_GUNW_032_083_D_093_033_4000_SH_20261005T232445_20261005T232520_20261017T232445_20261017T232520_P05023_N_F_J_001.h5"
    BBOX = [-76.30, -9.98, -76.18, -9.88]
    STATIC = Path(__file__).resolve().parents[1] / "backend" / "static"

    print("Leyendo coherencia GUNW sobre Huánuco…")
    coh = resumen_coherencia(str(GUNW), BBOX)
    print(json.dumps(coh, indent=2, ensure_ascii=False))
    coh["zona"] = "Huánuco"
    (STATIC / "coherencia_huanuco.json").write_text(json.dumps(coh, ensure_ascii=False, indent=2))

    # fusión con el cambio ya calculado
    camb = json.load(open(STATIC / "change_gcov_t83.json")).get("stats", {})
    fus = fusionar(camb, coh)
    print("\nFUSIÓN:")
    print(json.dumps(fus, indent=2, ensure_ascii=False))
    (STATIC / "fusion_huanuco.json").write_text(json.dumps(fus, ensure_ascii=False, indent=2))
