"""Qaway — Módulo de terreno: auto-descarga DEM (Copernicus GLO-30) + pendiente.

El DEM Copernicus GLO-30 está en un bucket público de AWS (sin login) → Qaway lo baja
automáticamente para el área del usuario, como ya hace con NISAR. La pendiente del terreno
es un factor clave de susceptibilidad a deslizamientos (ladera empinada + cambio = riesgo).

Fuente: https://copernicus-dem-30m.s3.amazonaws.com  (COG, EPSG:4326, ~30 m)
"""
from __future__ import annotations

import math
import os

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.windows import from_bounds

# Lectura remota de COG sin credenciales
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

BASE = "https://copernicus-dem-30m.s3.amazonaws.com"


def _tile_name(lat_sw: int, lon_sw: int) -> str:
    ns = "N" if lat_sw >= 0 else "S"
    ew = "E" if lon_sw >= 0 else "W"
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat_sw):02d}_00_{ew}{abs(lon_sw):03d}_00_DEM"


def _tiles_for_bbox(bbox):
    W, S, E, N = bbox
    tiles = []
    for lat in range(math.floor(S), math.floor(N) + 1):
        for lon in range(math.floor(W), math.floor(E) + 1):
            tiles.append((lat, lon))
    return tiles


def obtener_dem(bbox):
    """Devuelve (dem, transform) recortado al bbox lon/lat, auto-descargando los tiles."""
    srcs = []
    for lat, lon in _tiles_for_bbox(bbox):
        name = _tile_name(lat, lon)
        url = f"/vsicurl/{BASE}/{name}/{name}.tif"
        try:
            srcs.append(rasterio.open(url))
        except Exception:
            pass  # tile inexistente (océano) → se omite
    if not srcs:
        raise RuntimeError("No se encontró DEM para esa zona.")
    W, S, E, N = bbox
    mosaic, transform = merge(srcs, bounds=(W, S, E, N))
    for s in srcs:
        s.close()
    return mosaic[0].astype("float32"), transform


def calcular_pendiente(dem, transform, lat_centro):
    """Pendiente en grados a partir del DEM (EPSG:4326). Convierte grados→metros."""
    dlon = abs(transform.a)  # grados/px en X
    dlat = abs(transform.e)  # grados/px en Y
    mx = dlon * 111320.0 * math.cos(math.radians(lat_centro))  # m/px en X
    my = dlat * 110540.0                                       # m/px en Y
    dem = np.where(np.isfinite(dem), dem, np.nan)
    gy, gx = np.gradient(dem, my, mx)
    slope = np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy)))
    return slope


def resumen_terreno(bbox):
    """Resumen de terreno para el agente: pendientes y % de laderas empinadas."""
    dem, transform = obtener_dem(bbox)
    lat_c = (bbox[1] + bbox[3]) / 2
    slope = calcular_pendiente(dem, transform, lat_c)
    valid = np.isfinite(slope)
    if not valid.any():
        return {"error": "sin datos de terreno"}
    s = slope[valid]
    n = s.size
    return {
        "elevacion_min_m": round(float(np.nanmin(dem)), 1),
        "elevacion_max_m": round(float(np.nanmax(dem)), 1),
        "pendiente_media_grados": round(float(s.mean()), 1),
        "pendiente_max_grados": round(float(s.max()), 1),
        "pct_laderas_empinadas_>25deg": round(100.0 * np.count_nonzero(s > 25) / n, 1),
        "pct_laderas_muy_empinadas_>35deg": round(100.0 * np.count_nonzero(s > 35) / n, 1),
        "fuente": "Copernicus GLO-30 DEM (~30 m)",
    }


if __name__ == "__main__":
    import json
    BBOX = [-76.30, -9.98, -76.18, -9.88]  # Huánuco
    print("Auto-descargando DEM y calculando pendiente sobre Huánuco…")
    print(json.dumps(resumen_terreno(BBOX), indent=2, ensure_ascii=False))
