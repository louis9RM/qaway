"""Carga de configuración de SARvigía.

Separa configuración pública (config.yaml, versionada) de secretos
(secrets.yaml, NUNCA versionado). El token también puede venir de la
variable de entorno EARTHDATA_TOKEN, que tiene prioridad.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# Raíz del proyecto = carpeta que contiene /config y /mcp_server
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
SECRETS_FILE = CONFIG_DIR / "secrets.yaml"


def load_config() -> dict[str, Any]:
    """Lee config.yaml (público)."""
    with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def get_token() -> str:
    """Devuelve el token de Earthdata.

    Prioridad: variable de entorno EARTHDATA_TOKEN > config/secrets.yaml.
    Lanza un error claro si no se encuentra (sin exponer el valor).
    """
    env_token = os.environ.get("EARTHDATA_TOKEN")
    if env_token:
        return env_token.strip()

    if SECRETS_FILE.exists():
        with open(SECRETS_FILE, "r", encoding="utf-8") as fh:
            secrets = yaml.safe_load(fh) or {}
        token = (secrets.get("earthdata_token") or "").strip()
        if token and token != "PEGA_AQUI_TU_TOKEN":
            return token

    raise RuntimeError(
        "No se encontró el token de Earthdata. "
        "Crea config/secrets.yaml (copia secrets.yaml.example) y pega tu token, "
        "o exporta la variable de entorno EARTHDATA_TOKEN."
    )


def get_data_dir() -> Path:
    cfg = load_config()
    data_dir = Path(cfg.get("data_dir", "./data"))
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
