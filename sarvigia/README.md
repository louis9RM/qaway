# SARvigía — Módulo MCP (acceso a datos SAR / NISAR)

> *"El centinela de radar que vigila tus cerros."*
> Parte del proyecto **SARvigía** para el NASA Space Apps Challenge (reto NISAR).

Este módulo expone, vía **MCP (Model Context Protocol)**, herramientas para que un
asistente de IA (p. ej. Claude) **busque y descargue datos SAR de ASF** de forma
conversacional. Es la capa de datos del sistema.

## Estructura

```
sarvigia/
├── config/
│   ├── config.yaml            # Config pública (zonas, dataset, data_dir) — SÍ va a git
│   ├── secrets.yaml           # TOKEN Earthdata — NO va a git (.gitignore, perms 600)
│   └── secrets.yaml.example   # Plantilla
├── mcp_server/
│   ├── config.py              # Carga config + token (env EARTHDATA_TOKEN tiene prioridad)
│   ├── asf_client.py          # Búsqueda (bbox / gránulo) + descarga vía asf_search
│   └── server.py              # Servidor MCP (MCPServer) con las herramientas
├── tools/
│   └── migrar_token.py        # Utilidad: mueve el token desde un script a secrets.yaml
├── data/                      # Escenas descargadas (NO va a git)
└── requirements.txt
```

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración del token (una sola vez)

Opción A — copiar la plantilla y pegar el token:
```bash
cp config/secrets.yaml.example config/secrets.yaml
# edita config/secrets.yaml y pega tu token de Earthdata
chmod 600 config/secrets.yaml
```

Opción B — migrar el token desde un script existente (p. ej. `descarga.py`):
```bash
python tools/migrar_token.py /ruta/a/descarga.py
```

Opción C — variable de entorno (tiene prioridad sobre el archivo):
```bash
export EARTHDATA_TOKEN="...."
```

> 🔐 El token **nunca** se versiona. `config/secrets.yaml` está en `.gitignore`.
> Genera/rota tu token en https://urs.earthdata.nasa.gov → *Generate Token*.

## Herramientas MCP expuestas

| Herramienta | Qué hace |
|---|---|
| `listar_zonas` | Lista las zonas monitoreadas configuradas (Chaglla, Huánuco–Pucallpa). |
| `buscar_escenas_zona` | Busca escenas NISAR sobre una zona configurada (fechas opcionales). |
| `buscar_escenas_bbox` | Busca escenas sobre un bbox arbitrario `[lon_min, lat_min, lon_max, lat_max]`. |
| `buscar_por_granulo` | Busca escenas por nombre(s) de gránulo. |
| `descargar_escena` | Descarga escena(s) por nombre de gránulo a `data/`. |

## Ejecutar el servidor MCP

```bash
python -m sarvigia.mcp_server.server     # transporte stdio por defecto
```

Para conectarlo a Claude Desktop/Code, apúntalo a ese comando como servidor MCP stdio.

## Estado

- ✅ Config pública + secretos separados; token seguro (perms 600, gitignored).
- ✅ Cliente ASF: búsqueda por bbox y por gránulo, descarga autenticada.
- ✅ Servidor MCP (mcp 2.x / `MCPServer`) con 5 herramientas.
- ✅ Probado en vivo: búsqueda NISAR GCOV sobre Chaglla (oct 2026) → 6 escenas.

## Nota técnica

Dataset por defecto: **NISAR**, nivel **GCOV** (Geocoded Covariance), que es el que
ya se procesa en los scripts de análisis (lectura de `science/LSAR/GCOV/grids/frequencyA`,
polarización HH/VV, umbral de agua en banda L ~ -13.5 dB). Como respaldo, el dataset
puede cambiarse en `config.yaml` a Sentinel-1 o ALOS PALSAR (banda L) sin tocar el código.
```
