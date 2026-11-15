"""Servidor MCP de SARvigía.

Expone herramientas para que un asistente (p.ej. Claude) consulte y descargue
datos SAR de ASF de forma conversacional:

  - listar_zonas            : zonas monitoreadas configuradas
  - buscar_escenas_zona     : busca escenas NISAR sobre una zona configurada
  - buscar_escenas_bbox     : busca escenas sobre un bbox arbitrario
  - buscar_por_granulo      : busca por nombre(s) de gránulo
  - descargar_escena        : descarga escena(s) por nombre de gránulo

Ejecutar:  python -m sarvigia.mcp_server.server
"""
from __future__ import annotations

from typing import Any, Optional

from mcp.server.mcpserver import MCPServer

from . import asf_client
from . import config as cfg

mcp = MCPServer("SARvigía")


@mcp.tool()
def listar_zonas() -> dict[str, Any]:
    """Lista las zonas monitoreadas ('hot zones') configuradas en config.yaml."""
    return cfg.load_config().get("zonas", {})


@mcp.tool()
def buscar_escenas_zona(
    zona: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: Optional[str] = None,
    processing_level: Optional[str] = None,
) -> dict[str, Any]:
    """Busca escenas SAR sobre una zona configurada (p.ej. 'chaglla').

    start/end: fechas ISO 'YYYY-MM-DD'. dataset por defecto: NISAR.
    """
    zonas = cfg.load_config().get("zonas", {})
    if zona not in zonas:
        return {"error": f"Zona '{zona}' no existe.", "zonas_disponibles": list(zonas)}
    bbox = zonas[zona]["bbox"]
    escenas = asf_client.search_by_bbox(
        bbox, start=start, end=end, dataset=dataset, processing_level=processing_level
    )
    return {"zona": zona, "bbox": bbox, "total": len(escenas), "escenas": escenas}


@mcp.tool()
def buscar_escenas_bbox(
    bbox: list[float],
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: Optional[str] = None,
    processing_level: Optional[str] = None,
) -> dict[str, Any]:
    """Busca escenas SAR sobre un bbox [lon_min, lat_min, lon_max, lat_max] (EPSG:4326)."""
    escenas = asf_client.search_by_bbox(
        bbox, start=start, end=end, dataset=dataset, processing_level=processing_level
    )
    return {"bbox": bbox, "total": len(escenas), "escenas": escenas}


@mcp.tool()
def buscar_por_granulo(granulos: list[str]) -> dict[str, Any]:
    """Busca escenas por nombre(s) de gránulo."""
    escenas = asf_client.search_by_granules(granulos)
    return {"total": len(escenas), "escenas": escenas}


@mcp.tool()
def descargar_ultimas_fechas_zona(
    zona: str,
    n: int = 2,
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: Optional[str] = None,
    processing_level: Optional[str] = None,
) -> dict[str, Any]:
    """Descarga las `n` últimas fechas COMPARABLES (misma geometría) de una zona configurada.

    Ideal para detección de cambios: por defecto baja las 2 últimas fechas del
    mismo track/dirección, que SÍ se pueden comparar entre sí.
    """
    zonas = cfg.load_config().get("zonas", {})
    if zona not in zonas:
        return {"error": f"Zona '{zona}' no existe.", "zonas_disponibles": list(zonas)}
    return asf_client.descargar_ultimas_fechas(
        zonas[zona]["bbox"], n=n, start=start, end=end,
        dataset=dataset, processing_level=processing_level,
    )


@mcp.tool()
def descargar_ultimas_fechas_bbox(
    bbox: list[float],
    n: int = 2,
    start: Optional[str] = None,
    end: Optional[str] = None,
    dataset: Optional[str] = None,
    processing_level: Optional[str] = None,
) -> dict[str, Any]:
    """Descarga las `n` últimas fechas COMPARABLES (misma geometría) sobre un bbox arbitrario."""
    return asf_client.descargar_ultimas_fechas(
        bbox, n=n, start=start, end=end,
        dataset=dataset, processing_level=processing_level,
    )


@mcp.tool()
def descargar_escena(granulos: list[str]) -> dict[str, Any]:
    """Descarga escena(s) por nombre de gránulo a la carpeta de datos configurada.

    OJO: las escenas NISAR GCOV pesan varios GB; la descarga puede tardar.
    """
    return asf_client.download_granules(granulos)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
