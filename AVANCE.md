# Qaway — Estado del proyecto (avance)

> Última actualización: 2026-11-14 (noche)
> Reto: **NASA Space Apps 2026 — "Dancing with the SARs"** (NISAR).
> Equipo: **thecreator** — Lino Ever Ramos Maíz · Silvana Rossío Pacheco Malpartida.
> Producto: **Qaway** (*"el que vigila"* en quechua) — app web que convierte el radar
> NISAR en **alertas de peligro por voz** para carreteras andinas del Perú.
> 🔗 Demo público: **https://qaway.thecreatorcampus.ai**

---

## ✅ Lo que YA funciona (end-to-end, probado)

**Detecta 3 tipos de desastre** a lo largo de las carreteras:
1. 🏔️ **Deslizamientos** (ya ocurridos) — cambio de superficie (log-ratio + Wishart).
2. 📉 **Movimiento lento de laderas** (alerta temprana, mm/semana) — InSAR (GUNW).
3. 🌊 **Inundación / crecida de río** — Otsu + cambio (método NASA ARSET).

**2 modalidades de uso:**
- 🎙️ **Por voz** (conductor, manos libres): pregunta → GPS → corredor de carretera → analiza → **responde hablando**.
- ✏️ **Dibujar polígono** (analista): marca un área → analiza esa zona exacta.

**Agente de IA agentic (el gancho):** LLM local **Ollama/Qwen2.5** con tool-calling;
entiende cualquier pregunta (ES/EN, simple/técnico), **decide qué análisis correr** y narra
por voz. 7 herramientas. Auto-reintento si el modelo se traba.

**Pipeline real:** dibujar/voz → `/api/buscar` (ASF, 2 últimas fechas auto) → `/api/analisis`
(descarga GCOV+GUNW, recorta el polígono, procesa cambio+deformación+coherencia+inundación) →
el agente narra. Caché LRU 100 GB (limpieza auto, demo Huánuco protegida).

**Datos reales:** NISAR GCOV/GUNW (ASF) + Copernicus GLO-30 DEM (pendiente). Mapa OSM.
(⚠️ borré y re-descargué data probando Aguaytía — funciona la descarga en zona nueva ~4-15 min.)

**Despliegue:** Docker (frontend nginx :8101 + backend FastAPI :8100) + Cloudflare Tunnel.
Ollama corre en el host (GPU RTX 2070). El backend lo alcanza vía `host.docker.internal`.

---

## 📁 Estructura clave
```
sarvigia/                         (carpeta histórica; el producto es Qaway)
├── frontend/   index.html, js/app.js (?v=30), js/config.js   # UI en INGLÉS, EN por defecto
├── backend/    app.py, agent.py, limpieza.py, Dockerfile, static/
├── mcp_server/ asf_client.py      # búsqueda/descarga NISAR (NO usa protocolo MCP, es módulo py)
├── processing/ backscatter_cd.py, deformacion.py, coherence_cd.py, inundacion.py, terreno.py
├── deploy/     docker-compose.yml  # OLLAMA_HOST, QAWAY_CACHE_MAX_GB=100
└── data/       escenas .h5 (caché)
arquitectura/   ADD.md, ArchitecturalDrivers.md, Design/{Architecture, IterationPlan, Iteration1..6}.md
documentacion/  presentacion_qaway.md, video_script_qaway.md, Qaway_demo.pdf, GUIA_PRUEBA_EQUIPO.md
```

---

## 🔌 Cómo volver a levantar (tras prender la PC)
```bash
# 1) cloudflared y Ollama se autoarrancan. Verifica:
sudo systemctl status cloudflared
curl -s http://127.0.0.1:11434/api/tags >/dev/null && echo "Ollama OK"

# 2) Levantar Qaway (si los contenedores no están arriba)
cd ~/robotica-remota/spaceapps/sarvigia/deploy && docker compose up -d

# 3) Verificar
curl -s http://127.0.0.1:8100/api/health        # backend → {"ok":true,"service":"qaway-backend"}
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8101/   # frontend 200
```
> Los contenedores tienen `restart: unless-stopped` → sobreviven hibernación/reinicio.
> Solo si apagas del todo hay que `docker compose up -d`.
> ⚠️ El link público vive mientras la PC esté encendida + túnel arriba.

---

## 📋 Entregables para el formulario de NASA (listos / pendientes)
- ✅ **Resumen** (inglés, ~150 palabras) — en el chat.
- ✅ **Demo:** `documentacion/Qaway_demo.pdf` (7 páginas, con screenshot real + diagrama de arquitectura). → subir a Drive/GitHub público.
- ✅ **Proyecto:** https://qaway.thecreatorcampus.ai
- ⬜ **Detalles del proyecto** (campo largo) — falta redactar (en inglés).
- ⬜ **Uso de SI:** marcar LLM/chatbot (Qwen2.5 agente + NotebookLM/Claude redacción) + imagen (si usaras Gemini).
- ⬜ **Datos NASA:** NISAR (ASF), NISAR Cookbook, ARSET flood, White Paper Landslides.
- ⬜ **Otros datos:** Copernicus DEM, OSM/Overpass, MapLibre/Turf, Ollama/Qwen2.5.
- 🟢 **Marca de agua:** solo si usaras imágenes de IA (decidiste NO usar la de Gemini → el PDF no necesita marca).

---

## ⏳ Pendientes / ideas (si hay tiempo)
- 🎥 Video de 30s (hay `video_script_qaway.md` + prompt para NotebookLM).
- 🌧️ Módulo de lluvia GPM (driver físico) — no construido.
- 🗺️ Mostrar el overlay de cambio REAL sobre el mapa (hoy el diagnóstico es por voz).
- 🧠 Deformación con serie de tiempo (dolphin/SBAS, GPU) — hoy es par único (indicativo).
- 💾 Jobs en Redis/Postgres (hoy en memoria, se pierden al reiniciar).
- 📶 Offline-first (pre-cachear ruta + alerta sin señal) — solo diseñado.

---

## 📌 Notas clave (honestas, para el pitch)
- **NO decir "funciona sin internet"** — hoy necesita internet; el offline es diseño/futuro.
- **NO decir que usa MCP** — el agente es Ollama local con tool-calling, no MCP.
- Deformación de 1 par = **"indicio"**, no medición certificada (serie de tiempo lo confirmaría).
- Inundación confiable en **ríos/zonas abiertas**; difícil en ciudad densa.
- Copernicus DEM es **ESA**, no NASA → va en "otros datos".
