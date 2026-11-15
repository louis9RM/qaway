"""Qaway — Módulo de procesamiento: detección de cambios de retrodispersión (GCOV).

Método (respaldo científico):
  1) LOG-RATIO en dB (método oficial ASF/NASA, Meyer et al., "NISAR GCOV SAR
     Change Detection Methods"): dB2 - dB1 sobre la potencia total (HHHH+HVHV).
  2) Test estadístico de WISHART/CONRADSEN (IEEE TGRS 2003/2016): significancia
     por píxel con tasa de falsa alarma controlada (alpha) → quita el "ruido".
  Se marca CAMBIO donde el test es significativo (p < alpha); el signo (aumento/
  disminución de retrodispersión) viene del log-ratio.

Entrada : dos escenas GCOV (.h5) de la MISMA geometría (track/órbita), + bbox lon/lat.
Salida  : GeoTIFF (UTM) + PNG RGBA (overlay MapLibre) + JSON (esquinas lon/lat + stats).

Uso:
  python3 -I backscatter_cd.py                      # corre el par track 83 (demo Huánuco)
  from backscatter_cd import detect_change, render  # como módulo
"""
from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer
from scipy.stats import chi2

GCOV_GRID = "science/LSAR/GCOV/grids/frequencyA"


# ----------------------------------------------------------------------------
# Lectura + recorte
# ----------------------------------------------------------------------------
def _read_window(h5_path: str, bbox_lonlat, pad_px: int = 0):
    """Abre un GCOV y recorta la ventana que cubre bbox_lonlat=[W,S,E,N].
    Devuelve dict con HHHH, HVHV, looks, mask, extent UTM y epsg."""
    with h5py.File(h5_path, "r") as h5:
        g = h5[GCOV_GRID]
        x = g["xCoordinates"][:]            # UTM X (m)
        y = g["yCoordinates"][:]            # UTM Y (m)
        epsg = int(np.array(g["projection"]).item())

        # bbox lon/lat -> UTM del producto
        tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
        W, S, E, N = bbox_lonlat
        xs, ys = tr.transform([W, E, W, E], [S, S, N, N])
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        xi = np.where((x >= xmin) & (x <= xmax))[0]
        yi = np.where((y >= ymin) & (y <= ymax))[0]
        if xi.size == 0 or yi.size == 0:
            raise ValueError("El bbox no intersecta la escena GCOV.")
        x0, x1 = int(xi.min()) - pad_px, int(xi.max()) + 1 + pad_px
        y0, y1 = int(yi.min()) - pad_px, int(yi.max()) + 1 + pad_px
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(len(x), x1), min(len(y), y1)

        out = {
            "HHHH": g["HHHH"][y0:y1, x0:x1].astype(np.float32),
            "epsg": epsg,
            "x": x[x0:x1], "y": y[y0:y1],
        }
        out["HVHV"] = g["HVHV"][y0:y1, x0:x1].astype(np.float32) if "HVHV" in g else None
        out["looks"] = g["numberOfLooks"][y0:y1, x0:x1].astype(np.float32) if "numberOfLooks" in g else None
        out["mask"] = g["mask"][y0:y1, x0:x1] if "mask" in g else None
        return out


# ----------------------------------------------------------------------------
# Núcleo: log-ratio (ASF) + Wishart (Conradsen)
# ----------------------------------------------------------------------------
def detect_change(h5_a: str, h5_b: str, bbox_lonlat, alpha: float = 0.01):
    """Compara dos GCOV. Devuelve arrays, extent UTM, epsg y estadísticas."""
    A = _read_window(h5_a, bbox_lonlat)
    B = _read_window(h5_b, bbox_lonlat)

    # alinear tamaños (por bordes de recorte distintos)
    h = min(A["HHHH"].shape[0], B["HHHH"].shape[0])
    w = min(A["HHHH"].shape[1], B["HHHH"].shape[1])
    def crop(a): return None if a is None else a[:h, :w]
    hh_a, hh_b = crop(A["HHHH"]), crop(B["HHHH"])
    hv_a, hv_b = crop(A["HVHV"]), crop(B["HVHV"])
    looks = crop(A["looks"])
    xcoords, ycoords = A["x"][:w], A["y"][:h]
    epsg = A["epsg"]

    # potencia total (canales disponibles)
    chans_a = [c for c in (hh_a, hv_a) if c is not None]
    chans_b = [c for c in (hh_b, hv_b) if c is not None]
    p = len(chans_a)
    pow_a = np.add.reduce(chans_a)
    pow_b = np.add.reduce(chans_b)

    valid = np.isfinite(pow_a) & np.isfinite(pow_b) & (pow_a > 0) & (pow_b > 0)
    if A["mask"] is not None and B["mask"] is not None:
        # NISAR GCOV mask: 1 = dato válido, 0 = nodata, 255 = relleno fuera del swath.
        valid &= (crop(A["mask"]) != 255) & (crop(B["mask"]) != 255)

    # ---- 1) LOG-RATIO en dB (ASF/Meyer) ----
    ratio_db = np.full((h, w), np.nan, np.float32)
    ratio_db[valid] = 10.0 * np.log10(pow_b[valid] / pow_a[valid])

    # ---- 2) Test de WISHART/CONRADSEN pareado (caso diagonal, p canales) ----
    # looks equivalentes por píxel (si no hay, usar un valor típico GCOV)
    n = looks.copy() if looks is not None else np.full((h, w), 12.0, np.float32)
    n = np.where(np.isfinite(n) & (n >= 1), n, np.nan)

    # -2 ln Q = -2 * sum_i n*(2 ln2 + ln x_i + ln y_i - 2 ln(x_i+y_i))
    lnQ = np.zeros((h, w), np.float32)
    for xa, xb in zip(chans_a, chans_b):
        with np.errstate(divide="ignore", invalid="ignore"):
            term = 2.0 * np.log(2.0) + np.log(xa) + np.log(xb) - 2.0 * np.log(xa + xb)
        lnQ += n * term
    stat = -2.0 * lnQ
    rho = 1.0 - 1.0 / (4.0 * n)          # corrección de Bartlett (p=1 por canal)
    stat_c = stat * rho
    dof = p                               # grados de libertad = nº de canales (diagonal)
    pval = np.full((h, w), np.nan, np.float32)
    ok = valid & np.isfinite(n) & np.isfinite(stat_c) & (stat_c >= 0)
    pval[ok] = chi2.sf(stat_c[ok], dof)

    change = ok & (pval < alpha)          # cambio estadísticamente significativo

    # estadísticas
    dx = abs(float(xcoords[1] - xcoords[0])) if len(xcoords) > 1 else 10.0
    dy = abs(float(ycoords[1] - ycoords[0])) if len(ycoords) > 1 else 10.0
    px_area = dx * dy
    stats = {
        "alpha": alpha,
        "metodo": "ASF log-ratio dB + Wishart/Conradsen (significancia por pixel)",
        "polarizaciones": ["HHHH", "HVHV"][:p],
        "px_validos": int(valid.sum()),
        "px_cambio": int(change.sum()),
        "area_cambio_km2": round(float(change.sum()) * px_area / 1e6, 4),
        "pct_cambio": round(100.0 * change.sum() / max(1, valid.sum()), 3),
        "aumento_km2": round(float((change & (ratio_db > 0)).sum()) * px_area / 1e6, 4),
        "disminucion_km2": round(float((change & (ratio_db < 0)).sum()) * px_area / 1e6, 4),
    }
    extent_utm = [float(xcoords.min()), float(ycoords.min()),
                  float(xcoords.max()), float(ycoords.max())]
    return {"ratio_db": ratio_db, "change": change, "pval": pval,
            "x": xcoords, "y": ycoords, "epsg": epsg,
            "extent_utm": extent_utm, "stats": stats}


# ----------------------------------------------------------------------------
# Render: PNG RGBA + JSON (esquinas lon/lat para MapLibre) + GeoTIFF
# ----------------------------------------------------------------------------
def render(result, out_png: str, out_json: str, out_tif: str | None = None,
           db_clip: float = 6.0):
    from PIL import Image

    ratio = result["ratio_db"]
    change = result["change"]
    h, w = ratio.shape

    # colormap divergente SOLO en cambio significativo: rojo=aumento, azul=disminución
    rgba = np.zeros((h, w, 4), np.uint8)
    k = np.clip(np.nan_to_num(ratio) / db_clip, -1, 1)
    inc = change & (ratio > 0)
    dec = change & (ratio < 0)
    # aumento (rojo cálido)
    rgba[inc, 0] = 240
    rgba[inc, 1] = (90 * (1 - np.abs(k[inc]))).astype(np.uint8)
    rgba[inc, 2] = (70 * (1 - np.abs(k[inc]))).astype(np.uint8)
    rgba[inc, 3] = (120 + 120 * np.abs(k[inc])).astype(np.uint8)
    # disminución (azul frío)
    rgba[dec, 0] = (60 * (1 - np.abs(k[dec]))).astype(np.uint8)
    rgba[dec, 1] = (120 * (1 - np.abs(k[dec]))).astype(np.uint8)
    rgba[dec, 2] = 240
    rgba[dec, 3] = (120 + 120 * np.abs(k[dec])).astype(np.uint8)

    Image.fromarray(rgba, "RGBA").save(out_png)

    # esquinas UTM -> lon/lat (orden MapLibre: TL, TR, BR, BL)
    xmin, ymin, xmax, ymax = result["extent_utm"]
    tr = Transformer.from_crs(f"EPSG:{result['epsg']}", "EPSG:4326", always_xy=True)
    corners_utm = [(xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
    coordinates = [list(tr.transform(x, y)) for x, y in corners_utm]

    meta = {"png": Path(out_png).name, "coordinates": coordinates,
            "epsg": result["epsg"], "stats": result["stats"]}
    json.dump(meta, open(out_json, "w"), ensure_ascii=False, indent=2)

    if out_tif:
        try:
            import rasterio
            from rasterio.transform import from_bounds
            transform = from_bounds(xmin, ymin, xmax, ymax, w, h)
            with rasterio.open(out_tif, "w", driver="GTiff", height=h, width=w,
                               count=1, dtype="float32", crs=f"EPSG:{result['epsg']}",
                               transform=transform, nodata=np.nan) as dst:
                dst.write(ratio, 1)
        except Exception as e:  # noqa: BLE001
            print("GeoTIFF omitido:", e)
    return meta


# ----------------------------------------------------------------------------
# Demo CLI: par GCOV track 83 descending sobre Huánuco
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    DATA = Path(__file__).resolve().parents[1] / "data"
    A = DATA / "NISAR_L2_PR_GCOV_033_083_D_093_4005_DHDH_A_20261017T232445_20261017T232520_P05023_N_F_J_001.h5"
    B = DATA / "NISAR_L2_PR_GCOV_034_083_D_093_4005_DHDH_A_20261029T232446_20261029T232520_P05036_N_F_J_001.h5"
    # bbox de prueba: valle de Huánuco (lon/lat)  [W, S, E, N]
    BBOX = [-76.30, -9.98, -76.18, -9.88]

    OUT = Path(__file__).resolve().parents[1] / "backend" / "static"
    OUT.mkdir(parents=True, exist_ok=True)

    print("Procesando par GCOV track 83 (17-oct vs 29-oct) sobre Huánuco…")
    res = detect_change(str(A), str(B), BBOX, alpha=0.01)
    meta = render(res, str(OUT / "change_gcov_t83.png"),
                  str(OUT / "change_gcov_t83.json"),
                  str(OUT / "change_gcov_t83.tif"))
    print(json.dumps(meta["stats"], indent=2, ensure_ascii=False))
    print("coordinates (lon/lat):", meta["coordinates"])
    print("PNG+JSON en:", OUT)
