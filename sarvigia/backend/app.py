"""SARvigía — Backend API (orquestador).

Conecta el frontend con el módulo de datos (búsqueda + descarga ASF/NISAR).

Flujo:
  1) POST /api/buscar   -> fechas disponibles sobre el polígono (rápido, sin descargar)
  2) POST /api/analisis -> crea job async que descarga el/los gránulo(s) elegido(s)
  3) GET  /api/jobs/{id}-> estado/progreso del job

Nota: el procesamiento (recorte + detección de cambios/deformación) se añadirá
como paso siguiente del job; por ahora el job descarga los datos listos para procesar.
"""
from __future__ import annotations

import re
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# El módulo de datos vive en sarvigia/mcp_server (montado en /app/sarvigia)
sys.path.insert(0, "/app")
from sarvigia.mcp_server import asf_client as ac  # noqa: E402

app = FastAPI(title="SARvigía API", version="0.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---- estado de jobs (en memoria; 1 descarga a la vez) ----
JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
DOWNLOAD_SEM = threading.Semaphore(1)


def wkt_to_bbox(wkt: str) -> list[float]:
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", wkt)]
    lons = nums[0::2]
    lats = nums[1::2]
    return [min(lons), min(lats), max(lons), max(lats)]


# ---------- modelos ----------
class BuscarReq(BaseModel):
    wkt: Optional[str] = None
    bbox: Optional[list[float]] = None
    start: Optional[str] = None
    end: Optional[str] = None
    processing_level: Optional[str] = None  # GCOV (defecto) | GUNW | ...


class AnalisisReq(BaseModel):
    granulos: list[str]
    wkt: Optional[str] = None       # polígono del usuario, para recortar y procesar
    bbox: Optional[list[float]] = None


class PreguntarReq(BaseModel):
    pregunta: str
    idioma: str = "es"        # es | en
    nivel: str = "sencillo"   # sencillo | tecnico
    contexto: Optional[dict] = None


# ---------- endpoints ----------
@app.get("/api/health")
def health():
    return {"ok": True, "service": "qaway-backend"}


@app.post("/api/preguntar")
def preguntar(req: PreguntarReq):
    """Agente Qaway: responde en lenguaje natural (idioma + nivel elegidos)."""
    import agent  # módulo LLM (Ollama local)
    out = agent.responder(req.pregunta, idioma=req.idioma, nivel=req.nivel,
                          contexto=req.contexto)
    if out.get("respuesta") is None:
        raise HTTPException(503, out.get("error", "LLM no disponible"))
    return out


@app.post("/api/buscar")
def buscar(req: BuscarReq):
    bbox = req.bbox or (wkt_to_bbox(req.wkt) if req.wkt else None)
    if not bbox:
        raise HTTPException(400, "Falta 'wkt' o 'bbox'.")
    try:
        escenas = ac.search_by_bbox(
            bbox, start=req.start, end=req.end, processing_level=req.processing_level
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Error consultando ASF: {e}")

    grupos = ac._group_by_geometry(escenas)
    geometrias = []
    for (direccion, track), lista in grupos.items():
        geometrias.append({
            "direccion": direccion,
            "track": track,
            "etiqueta": f"{direccion} · track {track}",
            "fechas": [{"fecha": e["startTime"][:10], "granule": e["granule"]} for e in lista],
        })
    # geometría con cobertura más reciente primero
    geometrias.sort(key=lambda g: g["fechas"][-1]["fecha"] if g["fechas"] else "", reverse=True)
    return {"bbox": bbox, "total": len(escenas), "geometrias": geometrias}


@app.post("/api/analisis")
def analisis(req: AnalisisReq):
    if not req.granulos:
        raise HTTPException(400, "Falta 'granulos'.")
    bbox = req.bbox or (wkt_to_bbox(req.wkt) if req.wkt else None)
    job_id = uuid.uuid4().hex[:8]
    with JOBS_LOCK:
        JOBS[job_id] = {"id": job_id, "status": "queued", "progress": 0,
                        "step": "En cola", "granulos": req.granulos, "bbox": bbox,
                        "result": None, "error": None}
    threading.Thread(target=_run_job, args=(job_id,), daemon=True).start()
    return {"id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job no encontrado.")
    return job


def _set(job_id: str, **kw):
    with JOBS_LOCK:
        JOBS[job_id].update(kw)


def _run_job(job_id: str):
    granulos = JOBS[job_id]["granulos"]
    bbox = JOBS[job_id].get("bbox")
    _set(job_id, status="waiting", step="Esperando turno de descarga…", progress=5)
    with DOWNLOAD_SEM:  # una descarga a la vez para no saturar el servidor
        try:
            _set(job_id, status="running", step="Descargando datos NISAR desde ASF…", progress=20)
            res = ac.download_granules(granulos)
            _set(job_id, step="Procesando el polígono (detección de cambios NISAR)…", progress=70)
            stats = _procesar(granulos, res.get("destino"), bbox)
            if isinstance(stats, dict) and not stats.get("error"):
                _set(job_id, step="Midiendo deformación del terreno (InSAR GUNW)…", progress=85)
                gunw = _procesar_gunw(bbox)
                if gunw:
                    if gunw.get("deformacion"):
                        stats["deformacion"] = gunw["deformacion"]
                    if gunw.get("coherencia"):
                        stats["coherencia"] = gunw["coherencia"]
            _set(job_id, status="done", step="Análisis completo", progress=100,
                 result={"descarga": res, "stats": stats})
            try:  # limpieza de caché (borra escenas menos usadas si se pasa del límite)
                import limpieza
                limpieza.limpiar(res.get("destino") or "/app/sarvigia/data")
            except Exception:  # noqa: BLE001
                pass
        except Exception as e:  # noqa: BLE001
            _set(job_id, status="failed", step="Error en el análisis", error=str(e))


def _procesar(granulos, destino, bbox):
    """Recorta el polígono y corre la detección de cambios real sobre el par GCOV."""
    import sys
    from pathlib import Path
    if "/app/sarvigia/processing" not in sys.path:
        sys.path.insert(0, "/app/sarvigia/processing")
    import backscatter_cd as bcd

    if not bbox:
        return {"error": "Falta el polígono para recortar."}
    dest = Path(destino or "/app/sarvigia/data")
    # localizar los .h5 GCOV correspondientes a los gránulos
    gcov = []
    for g in granulos:
        for cand in (dest / f"{g}.h5", dest / g):
            if cand.exists() and "GCOV" in cand.name:
                gcov.append(cand); break
    if len(gcov) < 2:
        gcov = [p for p in dest.glob("*GCOV*.h5")
                if any(g[:45] in p.name for g in granulos)]
    gcov = sorted(set(str(p) for p in gcov))  # orden por fecha (nombre contiene AAAAMMDD)
    if len(gcov) < 2:
        return {"error": "Se necesitan 2 escenas GCOV comparables (misma geometría, 2 fechas)."}
    res = bcd.detect_change(gcov[0], gcov[1], bbox, alpha=0.01)
    stats = res["stats"]
    try:  # inundación / crecida de río (mismo par GCOV, método ARSET)
        import inundacion
        stats["inundacion"] = inundacion.detectar_inundacion(gcov[0], gcov[1], bbox)
    except Exception:  # noqa: BLE001
        pass
    try:
        import limpieza
        limpieza.marcar_uso(gcov)  # marca estas escenas como usadas (para el LRU)
    except Exception:  # noqa: BLE001
        pass
    return stats


def _procesar_gunw(bbox):
    """Descarga el GUNW más reciente de la zona y mide deformación (mm) + coherencia."""
    import sys
    from pathlib import Path
    if "/app/sarvigia/processing" not in sys.path:
        sys.path.insert(0, "/app/sarvigia/processing")
    try:
        escenas = ac.search_by_bbox(bbox, processing_level="GUNW")
    except Exception:  # noqa: BLE001
        return None
    if not escenas:
        return None
    latest = sorted(escenas, key=lambda e: e.get("startTime", ""))[-1]
    gran = latest.get("granule")
    if not gran:
        return None
    try:
        r = ac.download_granules([gran])
        dest = Path(r.get("destino") or "/app/sarvigia/data")
    except Exception:  # noqa: BLE001
        dest = Path("/app/sarvigia/data")
    f = None
    for cand in (dest / f"{gran}.h5", dest / gran):
        if cand.exists():
            f = str(cand); break
    if not f:
        cands = [p for p in dest.glob("*GUNW*.h5") if gran[:45] in p.name]
        f = str(cands[0]) if cands else None
    if not f:
        return None
    out = {}
    try:
        import deformacion
        out["deformacion"] = deformacion.resumen_deformacion(f, bbox)
    except Exception as e:  # noqa: BLE001
        out["deformacion"] = {"error": str(e)}
    try:
        import coherence_cd
        out["coherencia"] = coherence_cd.resumen_coherencia(f, bbox)
    except Exception:  # noqa: BLE001
        pass
    try:
        import limpieza
        limpieza.marcar_uso([f])
    except Exception:  # noqa: BLE001
        pass
    return out
