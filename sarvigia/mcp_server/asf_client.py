"""Cliente ASF para SARvigía.

Envuelve `asf_search` para:
  - autenticar con el token de Earthdata (vía config.get_token),
  - buscar escenas por área geográfica (bbox) y rango de fechas,
  - buscar escenas por nombre de gránulo,
  - descargar escenas a la carpeta de datos.

No imprime nunca el token.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import asf_search as asf

from . import config as cfg

# asf_search es muy verboso a nivel INFO; lo silenciamos para un MCP limpio.
logging.getLogger("asf_search").setLevel(logging.WARNING)


def _bbox_to_wkt(bbox: list[float]) -> str:
    """[lon_min, lat_min, lon_max, lat_max] -> polígono WKT."""
    lon_min, lat_min, lon_max, lat_max = bbox
    return (
        f"POLYGON(({lon_min} {lat_min}, {lon_max} {lat_min}, "
        f"{lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))"
    )


def get_session() -> asf.ASFSession:
    """Sesión autenticada con el token de Earthdata."""
    session = asf.ASFSession()
    session.auth_with_token(cfg.get_token())
    return session


def _result_to_dict(r: Any) -> dict[str, Any]:
    p = r.properties
    return {
        "granule": p.get("sceneName") or p.get("granuleName"),
        "platform": p.get("platform"),
        "processingLevel": p.get("processingLevel"),
        "startTime": p.get("startTime"),
        "stopTime": p.get("stopTime"),
        "polarization": p.get("polarization"),
        "path": p.get("pathNumber"),
        "frame": p.get("frameNumber"),
        "flightDirection": p.get("flightDirection"),
        "bytes": p.get("bytes"),
        "url": p.get("url"),
    }


def search_by_bbox(
    bbox: list[float],
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: Optional[str] = None,
    processing_level: Optional[str] = None,
    max_results: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Busca escenas que intersecten el bbox dado.

    bbox: [lon_min, lat_min, lon_max, lat_max] en EPSG:4326.
    start/end: fechas ISO (p.ej. '2026-10-01'). dataset: 'NISAR', etc.
    """
    conf = cfg.load_config().get("asf", {})
    dataset = dataset or conf.get("dataset", "NISAR")
    processing_level = processing_level or conf.get("processing_level")
    max_results = max_results or conf.get("max_results", 50)

    kwargs: dict[str, Any] = {
        "intersectsWith": _bbox_to_wkt(bbox),
        "dataset": dataset,
        "maxResults": max_results,
    }
    if start:
        kwargs["start"] = start
    if end:
        kwargs["end"] = end
    if processing_level:
        kwargs["processingLevel"] = processing_level

    results = asf.search(**kwargs)
    return [_result_to_dict(r) for r in results]


def search_by_granules(granules: list[str]) -> list[dict[str, Any]]:
    """Busca escenas por nombre(s) de gránulo (como en tu descarga.py)."""
    results = asf.granule_search(granules)
    return [_result_to_dict(r) for r in results]


def _group_by_geometry(escenas: list[dict[str, Any]]) -> dict[tuple, list[dict[str, Any]]]:
    """Agrupa escenas por (flightDirection, path) = geometría comparable."""
    from collections import defaultdict
    g: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for e in escenas:
        g[(e["flightDirection"], e["path"])].append(e)
    # ordenar cada grupo por fecha ascendente
    for k in g:
        g[k].sort(key=lambda e: e["startTime"] or "")
    return g


def descargar_ultimas_fechas(
    bbox: list[float],
    n: int = 2,
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: Optional[str] = None,
    processing_level: Optional[str] = None,
    out_dir: Optional[str] = None,
) -> dict[str, Any]:
    """Descarga las `n` últimas fechas COMPARABLES (misma geometría) sobre un bbox.

    1. Busca escenas sobre el bbox.
    2. Las agrupa por (dirección, track).
    3. Elige la geometría cuya fecha más reciente es la más nueva.
    4. Descarga sus `n` escenas más recientes (misma geometría = comparables).
    """
    escenas = search_by_bbox(
        bbox, start=start, end=end, dataset=dataset, processing_level=processing_level
    )
    if not escenas:
        return {"error": "No se encontraron escenas para la zona/fechas dadas.", "bbox": bbox}

    grupos = _group_by_geometry(escenas)
    # geometría con la fecha más reciente
    mejor = max(grupos.items(), key=lambda kv: kv[1][-1]["startTime"] or "")
    (direccion, track), lista = mejor
    seleccionadas = lista[-n:]  # las n más recientes de esa geometría
    nombres = [e["granule"] for e in seleccionadas]

    descarga = download_granules(nombres, out_dir=out_dir)
    return {
        "geometria": {"direccion": direccion, "track": track},
        "fechas": [e["startTime"][:10] for e in seleccionadas],
        "granulos": nombres,
        **descarga,
    }


def download_granules(granules: list[str], out_dir: Optional[str] = None) -> dict[str, Any]:
    """Descarga las escenas indicadas por nombre de gránulo.

    Devuelve un resumen (no descarga de nuevo lo ya presente si asf_search lo detecta).
    """
    session = get_session()
    out_path = Path(out_dir) if out_dir else cfg.get_data_dir()
    out_path.mkdir(parents=True, exist_ok=True)

    results = asf.granule_search(granules)
    found = [_result_to_dict(r) for r in results]
    results.download(path=str(out_path), session=session)

    return {
        "solicitadas": granules,
        "encontradas": len(found),
        "destino": str(out_path),
        "escenas": found,
    }
