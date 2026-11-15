"""Qaway — Módulo de DEFORMACIÓN (NISAR GUNW / InSAR) = ALERTA TEMPRANA.

Mientras backscatter_cd detecta el cambio DESPUÉS de que el terreno ya se movió,
la deformación InSAR mide el movimiento LENTO en milímetros ANTES del derrumbe:
convierte la fase interferométrica desenrollada (unwrappedPhase) en desplazamiento
en la línea de vista del radar.

    desplazamiento_LOS (m) = -(λ / 4π) · fase_desenrollada

λ = longitud de onda banda L de NISAR (~0.238 m). Se enmascara por coherencia (fiabilidad).
El desplazamiento es RELATIVO: se referencia a la mediana de la zona (terreno estable).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

GUNW = "science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram/HH"
LAMBDA_L = 0.238451  # m, banda L NISAR (fallback si no está en metadata)


def _crop(h5_path, bbox_lonlat):
    with h5py.File(h5_path, "r") as h5:
        g = h5[GUNW]
        x = g["xCoordinates"][:]
        y = g["yCoordinates"][:]
        epsg = int(np.array(g["projection"]).item())
        tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
        W, S, E, N = bbox_lonlat
        xs, ys = tr.transform([W, E, W, E], [S, S, N, N])
        xi = np.where((x >= min(xs)) & (x <= max(xs)))[0]
        yi = np.where((y >= min(ys)) & (y <= max(ys)))[0]
        if xi.size == 0 or yi.size == 0:
            raise ValueError("El bbox no intersecta el GUNW.")
        x0, x1 = int(xi.min()), int(xi.max()) + 1
        y0, y1 = int(yi.min()), int(yi.max()) + 1
        phase = g["unwrappedPhase"][y0:y1, x0:x1].astype(np.float32)
        coh = g["coherenceMagnitude"][y0:y1, x0:x1].astype(np.float32)
        # longitud de onda desde metadata si existe
        lam = LAMBDA_L
        try:
            lam = float(np.array(h5["science/LSAR/GUNW/grids/frequencyA/"
                                   "centerFrequency"]).item())
            lam = 299792458.0 / lam  # c/f → λ
        except Exception:
            pass
    return phase, coh, lam


def resumen_deformacion(h5_path, bbox_lonlat, dias=12, umbral_mm=10.0, coh_min=0.3):
    phase, coh, lam = _crop(h5_path, bbox_lonlat)
    valid = np.isfinite(phase) & np.isfinite(coh) & (coh >= coh_min) & (phase != 0)
    if valid.sum() < 20:
        return {"error": "coherencia insuficiente para medir deformación aquí."}
    # fase → desplazamiento LOS en mm
    disp_mm = -(lam / (4 * math.pi)) * phase * 1000.0
    # referencia relativa: restar la mediana (terreno estable = 0)
    ref = np.median(disp_mm[valid])
    disp_rel = disp_mm - ref
    d = disp_rel[valid]
    max_abs = float(np.nanmax(np.abs(d)))
    # signo del máximo (negativo = hundimiento/alejándose; positivo = levantándose)
    idx = np.nanargmax(np.abs(d))
    signo = "hundimiento/descenso" if d[idx] < 0 else "levantamiento"
    pct_mov = 100.0 * np.count_nonzero(np.abs(d) > umbral_mm) / d.size
    rate_semana = max_abs / dias * 7.0
    sev = "alta" if max_abs > 30 else ("media" if max_abs > 10 else "baja")
    return {
        "desplazamiento_max_mm": round(max_abs, 1),
        "tipo": signo,
        "tasa_mm_por_semana": round(rate_semana, 1),
        "pct_zona_en_movimiento_>%dmm" % int(umbral_mm): round(pct_mov, 1),
        "periodo_dias": dias,
        "severidad_deformacion": sev,
        "interpretacion": "movimiento lento del terreno (posible deslizamiento en curso)",
        "fuente": "NISAR GUNW · unwrappedPhase (InSAR banda L)",
    }


if __name__ == "__main__":
    DATA = Path(__file__).resolve().parents[1] / "data"
    G = DATA / "NISAR_L2_PR_GUNW_032_083_D_093_033_4000_SH_20261005T232445_20261005T232520_20261017T232445_20261017T232520_P05023_N_F_J_001.h5"
    BBOX = [-76.30, -9.98, -76.18, -9.88]
    STATIC = Path(__file__).resolve().parents[1] / "backend" / "static"
    print("Midiendo deformación InSAR sobre Huánuco (05→17 oct)…")
    r = resumen_deformacion(str(G), BBOX, dias=12)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    r["zona"] = "Huánuco"
    (STATIC / "deformacion_huanuco.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
