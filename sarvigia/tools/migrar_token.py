"""Utilidad: mueve el token de Earthdata desde descarga.py a config/secrets.yaml.

Uso:
    python tools/migrar_token.py /ruta/a/descarga.py

- Extrae el token (token = "...") del script indicado.
- Lo escribe en config/secrets.yaml con permisos 600.
- No imprime el token: solo longitud y una máscara.
Ejecútalo tú mismo; el token nunca sale de tu máquina.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python tools/migrar_token.py /ruta/a/descarga.py")
        return 1

    src_path = Path(sys.argv[1]).expanduser()
    if not src_path.exists():
        print(f"No existe: {src_path}")
        return 1

    src = src_path.read_text(encoding="utf-8")
    m = re.search(r'token\s*=\s*"([^"]+)"', src) or re.search(r"token\s*=\s*'([^']+)'", src)
    if not m:
        print("No se encontró un token (token = \"...\") en el archivo.")
        return 1

    tok = m.group(1).strip()
    out = PROJECT_ROOT / "config" / "secrets.yaml"
    out.write_text(
        "# SARvigía — SECRETOS (NO subir a git; está en .gitignore)\n"
        f'earthdata_token: "{tok}"\n',
        encoding="utf-8",
    )
    out.chmod(0o600)

    print(f"OK -> {out}")
    print(f"Longitud del token: {len(tok)} caracteres")
    print(f"Máscara: {tok[:6]}...{tok[-4:]}")
    print(f"Permisos: {oct(out.stat().st_mode)[-3:]}")
    print("\nRecuerda: considera revocar/rotar ese token si quedó en git en descarga.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
