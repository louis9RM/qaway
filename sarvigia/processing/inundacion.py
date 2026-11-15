"""Qaway — Módulo de INUNDACIÓN / crecida de ríos (GCOV).

Método oficial NASA ARSET (flood mapping con SAR):
  - El agua da retrodispersión MUY BAJA (oscura) → se separa con umbral automático de OTSU.
  - Se compara 2 fechas (misma geometría/órbita) → el agua NUEVA (que apareció en la fecha B
    y no estaba en la A) = inundación / desborde / crecida de río.
Fuente: NASA ARSET "SAR for Detecting and Monitoring Floods, Sea Ice, and Subsidence".

Entrada: par GCOV (.h5) misma geometría + bbox lon/lat.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

GRID = "science/LSAR/GCOV/grids/frequencyA"


def _leer_db(h5_path, bbox_lonlat):
    with h5py.File(h5_path, "r") as h5:
        g = h5[GRID]
        x = g["xCoordinates"][:]; y = g["yCoordinates"][:]
        epsg = int(np.array(g["projection"]).item())
        tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
        W, S, E, N = bbox_lonlat
        xs, ys = tr.transform([W, E, W, E], [S, S, N, N])
        xi = np.where((x >= min(xs)) & (x <= max(xs)))[0]
        yi = np.where((y >= min(ys)) & (y <= max(ys)))[0]
        if xi.size == 0 or yi.size == 0:
            raise ValueError("El bbox no intersecta la escena.")
        x0, x1 = int(xi.min()), int(xi.max()) + 1
        y0, y1 = int(yi.min()), int(yi.max()) + 1
        hh = g["HHHH"][y0:y1, x0:x1].astype(np.float32)
        hv = g["HVHV"][y0:y1, x0:x1].astype(np.float32) if "HVHV" in g else None
        mask = g["mask"][y0:y1, x0:x1] if "mask" in g else None
        dx = abs(float(g["xCoordinateSpacing"][()])); dy = abs(float(g["yCoordinateSpacing"][()]))
    pot = hh if hv is None else hh + hv
    valid = np.isfinite(pot) & (pot > 0)
    if mask is not None:
        valid &= (mask != 255)
    db = np.full(pot.shape, np.nan, np.float32)
    db[valid] = 10.0 * np.log10(pot[valid])
    return db, valid, dx * dy


def _otsu(v):
    """Umbral de Otsu sobre valores finitos (separa agua oscura de tierra)."""
    v = v[np.isfinite(v)]
    hist, edges = np.histogram(v, bins=256)
    centers = (edges[:-1] + edges[1:]) / 2
    w = hist.astype(np.float64); total = w.sum()
    if total == 0: return -13.5
    p = w / total
    omega = np.cumsum(p); mu = np.cumsum(p * centers)
    mu_t = mu[-1]
    denom = omega * (1 - omega)
    denom[denom == 0] = 1e-12
    sigma_b = (mu_t * omega - mu) ** 2 / denom
    return float(centers[np.nanargmax(sigma_b)])


def detectar_inundacion(h5_a, h5_b, bbox_lonlat):
    dbA, vA, pxA = _leer_db(h5_a, bbox_lonlat)
    dbB, vB, pxB = _leer_db(h5_b, bbox_lonlat)
    h = min(dbA.shape[0], dbB.shape[0]); w = min(dbA.shape[1], dbB.shape[1])
    dbA, dbB = dbA[:h, :w], dbB[:h, :w]; vA, vB = vA[:h, :w], vB[:h, :w]
    valid = vA & vB
    # umbral de agua (Otsu sobre ambas fechas juntas) — agua = por debajo del umbral
    thr = _otsu(np.concatenate([dbA[valid], dbB[valid]]))
    # agua calma en banda L suele estar por debajo de ~-15 dB; cap conservador para
    # evitar falsos positivos por sombra de radar en zona montañosa (debilidad ARSET).
    thr = min(thr, -15.0)
    aguaA = valid & (dbA < thr)
    aguaB = valid & (dbB < thr)
    nueva = aguaB & ~aguaA          # agua que apareció = inundación/crecida
    px_area = pxA
    km2 = lambda m: round(float(m.sum()) * px_area / 1e6, 4)
    return {
        "umbral_agua_dB": round(thr, 1),
        "agua_fecha_A_km2": km2(aguaA),
        "agua_fecha_B_km2": km2(aguaB),
        "agua_nueva_km2": km2(nueva),          # ← la crecida / inundación
        "pct_zona_inundada": round(100.0 * nueva.sum() / max(1, valid.sum()), 2),
        "metodo": "Umbral de Otsu + detección de cambios (NASA ARSET flood mapping)",
        "fuente": "NISAR GCOV banda L",
    }


if __name__ == "__main__":
    DATA = Path(__file__).resolve().parents[1] / "data"
    A = DATA / "NISAR_L2_PR_GCOV_033_083_D_093_4005_DHDH_A_20261017T232445_20261017T232520_P05023_N_F_J_001.h5"
    B = DATA / "NISAR_L2_PR_GCOV_034_083_D_093_4005_DHDH_A_20261029T232446_20261029T232520_P05036_N_F_J_001.h5"
    # bbox sobre el río Huallaga cerca de Huánuco
    BBOX = [-76.28, -9.98, -76.20, -9.90]
    print("Detectando agua/crecida sobre el río (17 vs 29-oct)…")
    print(json.dumps(detectar_inundacion(str(A), str(B), BBOX), indent=2, ensure_ascii=False))
