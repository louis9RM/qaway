# Qaway — Guía de prueba para el equipo

**App en vivo:** 👉 **https://qaway.thecreatorcampus.ai**
(ábrela en el celular; funciona con datos o wifi · usa **Chrome en Android** para la voz)

> ⚠️ Requiere que la PC de Ever esté encendida (servidor + Ollama + túnel Cloudflare).
> Si el link no carga, avisar a Ever.

---

## 1. El mapa (abajo a la izquierda, 3 botones)
- 🗺️ **Calles** (por defecto) — carreteras y nombres.
- 🛰️ **NASA Satélite** — imagen real NASA (MODIS) + carreteras encima.
- 🏔️ **NASA Relieve** — relieve andino NASA + carreteras encima.

## 2. Analizar una zona (dos formas)
- **GPS:** botón **📍 Usar mi ubicación** → Qaway busca la carretera cercana y dibuja un **corredor** (no un cuadrado).
- **Voz:** botón **🎙️ Preguntar por voz** y di *"analiza a 1 km a la redonda"*.
- (También: **✏️ Dibujar polígono** a mano, doble toque para cerrar.)

## 3. Hablar con el agente Qaway (lo más importante)
Arriba hay 2 toggles: **Idioma (ES/EN)** y **Nivel (Sencillo/Técnico)**.
Pregunta por **voz** 🎙️ o **texto** ⌨️. El agente **decide solo** qué datos consultar.

### Casos de uso para probar
| Pregunta | Qué hace el agente |
|---|---|
| *"¿Hay peligro en mi ruta?"* | Consulta el **cambio NISAR** (Wishart) → responde con datos |
| *"¿Por qué hay riesgo?"* | Consulta el **terreno/pendiente** (DEM) |
| *"¿Qué tan seguro estás de que hay deslizamiento?"* | **Fusión** intensidad + coherencia → nivel de confianza |
| *"¿Es seguro viajar de noche?"* | Razona con los datos |
| *"¿Quién eres?"* / *"Hola"* | Responde directo, **sin** consultar radar |

### Prueba los modos
- **Sencillo** → lenguaje de conductor (*"reduce la velocidad"*).
- **Técnico** → método, km², α, polarizaciones, banda L.
- **ES / EN** → cambia idioma de la respuesta **y de la voz**.

---

## Qué datos REALES usa Qaway (todo verificable)
- 🛰️ **NISAR GCOV** → detección de cambios (test de Wishart/Conradsen + método ASF/NASA).
- 🛰️ **NISAR GUNW** → coherencia (confirma el cambio).
- ⛰️ **DEM Copernicus GLO-30** → pendiente (susceptibilidad).
- 🗺️ **NASA GIBS** → mapas base satelitales.
- 🧠 **LLM local (Ollama qwen2.5)** → el cerebro del agente.

## Límites honestos (para no sorprenderse)
- La respuesta del agente tarda **~5 s** (modelo corre local).
- **Voz:** óptima en Chrome/Android; en iPhone usar el **campo de texto**.
- **NASA Satélite** se ve borrosa al acercar mucho (imagen global ~250 m) → usar "Calles" para detalle.
- Hoy el análisis usa la zona demo de **Huánuco** (par NISAR oct 2026); otras zonas requieren descargar su par.

---

## Si algo falla
- Link no carga → PC/túnel apagado (avisar a Ever).
- El agente no responde → backend u Ollama caídos (reiniciar en la PC).
- La voz no funciona → usar el campo de texto, o Chrome en Android.
