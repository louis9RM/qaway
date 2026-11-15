"""Qaway — Limpieza automática del caché de escenas NISAR (.h5 crudos, pesados).

Política (inteligente, no a ciegas):
  - Solo borra si el total supera MAX_GB (si hay espacio, no toca nada).
  - Borra las MENOS USADAS primero (por tiempo de último acceso), no las más viejas.
  - NUNCA borra las escenas "pin" (la demo de Huánuco) para no romper la presentación.
"""
from __future__ import annotations

import os
from pathlib import Path

MAX_GB = float(os.environ.get("QAWAY_CACHE_MAX_GB", "60"))
# Escenas protegidas (demo del jurado): no se borran jamás
PIN = ("_083_D_093_",)  # track 83 descending = par demo Huánuco (y su GUNW)


def _es_pin(nombre: str) -> bool:
    return any(p in nombre for p in PIN)


def marcar_uso(paths):
    """Marca archivos como 'usados ahora' (actualiza atime/mtime) para el LRU."""
    now = None
    for p in paths:
        try:
            os.utime(p, None)  # pone atime/mtime = ahora
        except OSError:
            pass


def limpiar(data_dir: str, max_gb: float = MAX_GB) -> dict:
    d = Path(data_dir)
    h5 = [p for p in d.glob("*.h5")]
    total = sum(p.stat().st_size for p in h5)
    cap = max_gb * (1024 ** 3)
    borrados = []
    if total <= cap:
        return {"borrados": [], "total_gb": round(total / 1024**3, 1), "accion": "nada (bajo el límite)"}
    # candidatos: no-pin, ordenados por menos usados (atime más antiguo primero)
    cand = sorted((p for p in h5 if not _es_pin(p.name)),
                  key=lambda p: p.stat().st_atime)
    for p in cand:
        if total <= cap:
            break
        sz = p.stat().st_size
        try:
            p.unlink()
            total -= sz
            borrados.append(p.name)
        except OSError:
            pass
    return {"borrados": borrados, "total_gb": round(total / 1024**3, 1),
            "accion": f"liberado hasta <= {max_gb} GB"}


if __name__ == "__main__":
    import json
    DATA = Path(__file__).resolve().parents[1] / "data"
    print(json.dumps(limpiar(str(DATA)), indent=2, ensure_ascii=False))
