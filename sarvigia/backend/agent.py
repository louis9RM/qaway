"""Qaway — Agente conversacional AGÉNTICO (cerebro LLM, en el backend).

No es un Q&A de respuestas fijas: el LLM es el ORQUESTADOR. Dada la pregunta del
usuario (en lenguaje natural), el agente DECIDE qué herramientas llamar (ej. ejecutar
la detección de cambios NISAR sobre su zona), las ejecuta, observa los resultados y
compone la respuesta razonando sobre datos REALES.

- Proveedor: Ollama local (reutiliza el patrón de aura-escritura-agentica). qwen2.5:7b
  soporta tool-calling vía /api/chat.
- idioma: 'es' | 'en'    nivel: 'sencillo' | 'tecnico'
- Modular: para añadir capacidades, agrega una función a TOOLS + _run_tool.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import urllib.error
import urllib.request

# Proveedor del LLM: "ollama" (local, GPU) | "gemini" (API en la nube, sin GPU)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("QAWAY_LLM_MODEL", "qwen2.5:7b")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("QAWAY_GEMINI_MODEL", "gemini-3.5-flash")
# Cadena de respaldo si el modelo principal está saturado (503/429) o lento.
GEMINI_FALLBACKS = [m.strip() for m in os.environ.get(
    "QAWAY_GEMINI_FALLBACKS", "gemini-3.1-flash-lite,gemini-3.6-flash").split(",") if m.strip()]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# modelo activo (para reportarlo en las respuestas)
MODEL = GEMINI_MODEL if LLM_PROVIDER == "gemini" else OLLAMA_MODEL

STATIC = pathlib.Path(__file__).resolve().parent / "static"


# ---------------------------------------------------------------------------
# Herramientas que el agente PUEDE decidir usar (modular: agrega más aquí)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analizar_cambios_nisar",
            "description": (
                "Ejecuta/consulta la detección de cambios de superficie (deslizamientos) con "
                "radar NISAR sobre la zona actual del usuario. Úsalo SIEMPRE que el usuario "
                "pregunte por peligro, riesgo, deslizamientos, seguridad o el estado de su "
                "ruta/zona, para responder con datos reales (área de cambio, significancia)."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_mi_zona",
            "description": (
                "Inicia el ANÁLISIS de radar NISAR alrededor de la ubicación del usuario "
                "(dibuja el corredor de la carretera y procesa cambio + deformación). Úsalo "
                "cuando el usuario pida analizar/escanear/revisar su zona o a X km a la redonda. "
                "Pasa 'km' si menciona una distancia (por defecto 1)."
            ),
            "parameters": {
                "type": "object",
                "properties": {"km": {"type": "number", "description": "radio en km (opcional)"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_hora",
            "description": (
                "Devuelve la fecha y hora local actual del usuario y el momento del día "
                "(madrugada / mañana / tarde / noche). Úsalo cuando pregunten la hora, la "
                "fecha, qué día es hoy, o para saludar según el momento del día."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_ubicacion",
            "description": (
                "Devuelve la ubicación aproximada del usuario (lugar, región, lat/lon) a partir de "
                "su GPS. Úsalo cuando pregunte dónde está, su ubicación, en qué lugar/región se "
                "encuentra, o para situar su análisis."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detectar_inundacion",
            "description": (
                "Detecta crecida de ríos / inundación / desborde de agua con radar NISAR "
                "(método NASA ARSET). Úsalo cuando el usuario pregunte por inundación, crecida "
                "del río, desborde, o si el agua subió cerca de la carretera."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "medir_deformacion",
            "description": (
                "ALERTA TEMPRANA: mide el movimiento LENTO del terreno en milímetros con InSAR "
                "(GUNW), ANTES de un derrumbe. Úsalo cuando el usuario pregunte si el cerro/terreno "
                "se está moviendo, hundiendo, deslizando lentamente, o por alerta temprana."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirmar_con_coherencia",
            "description": (
                "Devuelve el diagnóstico FUSIONADO de máxima precisión: combina el cambio de "
                "intensidad (Wishart) con la coherencia del radar (GUNW) para dar un nivel de "
                "CONFIANZA (alta/media/baja) y un veredicto. Úsalo cuando el usuario pida una "
                "confirmación, qué tan seguro es, o un diagnóstico definitivo del riesgo."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluar_terreno",
            "description": (
                "Consulta el terreno (pendiente/elevación del DEM Copernicus) de la zona del "
                "usuario. Úsalo cuando pregunten POR QUÉ hay riesgo, qué tan empinado es el "
                "terreno, o para explicar la susceptibilidad a deslizamientos (laderas "
                "empinadas + cambio = más riesgo)."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def _run_tool(name: str, args: dict, contexto: dict | None) -> dict:
    if name == "analizar_cambios_nisar":
        return _tool_cambios(contexto)
    if name == "evaluar_terreno":
        return _tool_terreno(contexto)
    if name == "confirmar_con_coherencia":
        return _tool_fusion(contexto)
    if name == "medir_deformacion":
        return _tool_deformacion(contexto)
    if name == "obtener_hora":
        return _tool_hora(contexto)
    if name == "obtener_ubicacion":
        return _tool_ubicacion(contexto)
    if name == "detectar_inundacion":
        return _tool_inundacion(contexto)
    return {"error": f"herramienta desconocida: {name}"}


def _tool_inundacion(contexto: dict | None) -> dict:
    """Crecida de ríos / inundación (agua nueva detectada con SAR, método ARSET)."""
    if contexto and isinstance(contexto.get("inundacion"), dict):
        return contexto["inundacion"]
    p = STATIC / "inundacion_huanuco.json"
    if not p.exists():
        return {"error": "sin datos de inundación para esta zona."}
    d = json.load(open(p))
    d["zona"] = (contexto or {}).get("zona", "la zona seleccionada")
    return d


def _parte_del_dia(h: int) -> tuple[str, str]:
    """Devuelve (es, en) del momento del día según la hora 0-23."""
    if h < 5:
        return ("madrugada", "night")
    if h < 12:
        return ("mañana", "morning")
    if h < 19:
        return ("tarde", "afternoon")
    return ("noche", "evening")


def _tool_hora(contexto: dict | None) -> dict:
    """Fecha/hora local del usuario y momento del día.
    Usa el reloj del dispositivo (el frontend lo pasa en contexto['tiempo']);
    si no está, cae al reloj del servidor."""
    t = (contexto or {}).get("tiempo") or {}
    hora = t.get("hora")
    if hora is None:
        now = datetime.datetime.now()
        hora = now.hour
        fecha = now.strftime("%Y-%m-%d")
        hhmm = now.strftime("%H:%M")
        fuente = "reloj del servidor"
    else:
        fecha = t.get("fecha") or ""
        hhmm = t.get("hhmm") or f"{int(hora):02d}:00"
        fuente = "reloj del dispositivo"
    es, en = _parte_del_dia(int(hora))
    return {"fecha": fecha, "hora_local": hhmm,
            "parte_del_dia_es": es, "parte_del_dia_en": en, "fuente": fuente}


def _tool_ubicacion(contexto: dict | None) -> dict:
    """Ubicación aproximada del usuario (desde el GPS del celular, vía el frontend)."""
    u = (contexto or {}).get("ubicacion")
    if not u or not isinstance(u, dict):
        return {"error": "No tengo tu ubicación. Activa el GPS o usa el botón 'Usar mi ubicación'."}
    return {"lugar": u.get("lugar") or "ubicación desconocida",
            "latitud": u.get("lat"), "longitud": u.get("lon"),
            "fuente": "GPS del dispositivo"}


def _tool_deformacion(contexto: dict | None) -> dict:
    """Movimiento lento del terreno en mm (InSAR GUNW) — alerta temprana."""
    p = STATIC / "deformacion_huanuco.json"
    if not p.exists():
        return {"error": "sin datos de deformación InSAR para esta zona."}
    d = json.load(open(p))
    d["zona"] = (contexto or {}).get("zona", "la zona seleccionada")
    d["nota"] = "estimación de un par interferométrico; una serie temporal lo confirmaría"
    return d


def _tool_fusion(contexto: dict | None) -> dict:
    """Diagnóstico fusionado (intensidad + coherencia) de máxima precisión."""
    p = STATIC / "fusion_huanuco.json"
    if not p.exists():
        return {"error": "aún no hay diagnóstico fusionado para esta zona."}
    f = json.load(open(p))
    f["zona"] = (contexto or {}).get("zona", "la zona seleccionada")
    return f


def _tool_terreno(contexto: dict | None) -> dict:
    """Pendiente/elevación reales (DEM Copernicus GLO-30) para explicar susceptibilidad."""
    p = STATIC / "terreno_huanuco.json"
    if not p.exists():
        return {"error": "sin datos de terreno para esta zona."}
    t = json.load(open(p))
    pend = float(t.get("pendiente_media_grados", 0))
    susc = "alta" if pend > 25 else ("media" if pend > 15 else "baja")
    t["susceptibilidad_por_pendiente"] = susc
    return t


def _tool_cambios(contexto: dict | None) -> dict:
    """Devuelve las estadísticas REALES del análisis de cambios NISAR.
    Hoy lee el resultado precomputado (par GCOV track 83, validado con Wishart).
    Futuro: ejecutar el procesamiento en vivo sobre contexto['bbox']."""
    # 1) si el frontend pasó stats EN VIVO del polígono analizado, usarlos
    if contexto and isinstance(contexto.get("stats_cambio"), dict):
        st = contexto["stats_cambio"]
    else:
        # 2) si no, el resultado precalculado de la zona demo
        p = STATIC / "change_gcov_t83.json"
        if not p.exists():
            return {"error": "aún no hay análisis; el usuario debe seleccionar un área o usar su GPS."}
        st = json.load(open(p)).get("stats", {})
    if not st:
        return {"error": "sin datos de cambio."}
    pct = float(st.get("pct_cambio", 0))      # ya está en %  (ej. 0.39 = 0.39%)
    area = float(st.get("area_cambio_km2", 0))
    # severidad calculada en código (no la inventa el LLM)
    if pct < 0.5:   sev = "bajo"
    elif pct < 2:   sev = "moderado"
    else:           sev = "alto"
    return {
        "zona": (contexto or {}).get("zona", "la zona seleccionada"),
        "fechas_comparadas": ["2026-10-17", "2026-10-29"],
        "sensor": "NISAR banda L (GCOV, track 83 descendente)",
        "metodo": st.get("metodo"),
        "polarizaciones": st.get("polarizaciones"),
        "significancia_alpha": st.get("alpha"),
        "area_cambiada_km2": round(area, 3),
        "porcentaje_del_area_analizada": f"{pct:.2f}%",   # etiquetado con unidad
        "aumento_retrodispersion_km2": st.get("aumento_km2"),
        "disminucion_retrodispersion_km2": st.get("disminucion_km2"),
        "nivel_severidad": sev,
    }


# ---------------------------------------------------------------------------
# System prompt (idioma + nivel)
# ---------------------------------------------------------------------------
def _system_prompt(idioma: str, nivel: str) -> str:
    lang = "español" if idioma == "es" else "English"
    if nivel == "tecnico":
        estilo = ("Answer with technical precision: method (ASF/NASA GCOV log-ratio dB + "
                  "Wishart/Conradsen test), changed area in km², significance alpha, HH/HV "
                  "polarizations, NISAR L-band. Be concise."
                  if idioma == "en" else
                  "Responde con precisión técnica: método (log-ratio dB de ASF/NASA + test de "
                  "Wishart/Conradsen), área de cambio en km², significancia alfa, polarizaciones "
                  "HH/HV, banda L de NISAR. Sé conciso.")
    else:
        estilo = ("Answer in very simple, practical language for a driver or citizen. Short "
                  "sentences, no jargon. Clearly say if there is danger and what to do."
                  if idioma == "en" else
                  "Responde en lenguaje muy simple y práctico, para un conductor o ciudadano. "
                  "Frases cortas, sin jerga. Di claramente si hay peligro y qué hacer.")
    rol = ("You are Qaway, a landslide-alert assistant for Andean roads in Peru, powered by NISAR "
           "satellite radar. You can CALL TOOLS to get real NISAR analysis before answering — use "
           "them when the question is about danger/risk/route. ALWAYS answer in "
           if idioma == "en" else
           "Eres Qaway, un asistente de alerta de deslizamientos para carreteras andinas del Perú, "
           "con radar satelital NISAR. Puedes LLAMAR HERRAMIENTAS para obtener el análisis real de "
           "NISAR antes de responder — úsalas cuando la pregunta sea sobre peligro/riesgo/ruta. "
           "Responde SIEMPRE en ")
    return f"{rol}{lang}. {estilo}"


# ---------------------------------------------------------------------------
# Capa de chat: formato canónico = estilo Ollama (messages con role/content/
# tool_calls). Cada proveedor convierte hacia/desde ese formato y devuelve
# siempre {"message": {"content": str, "tool_calls": [...]}}.
# ---------------------------------------------------------------------------
def _chat(messages: list[dict], tools=None, timeout: float = 60.0) -> dict:
    if LLM_PROVIDER == "gemini":
        return _chat_gemini(messages, tools, timeout)
    return _chat_ollama(messages, tools, timeout)


def _chat_ollama(messages: list[dict], tools=None, timeout: float = 60.0) -> dict:
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
               "options": {"temperature": 0.3}}
    if tools:
        payload["tools"] = tools
    req = urllib.request.Request(f"{OLLAMA_HOST}/api/chat",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _gemini_tools(tools) -> list | None:
    """Convierte las TOOLS (formato OpenAI/Ollama) a functionDeclarations de Gemini.
    Gemini rechaza 'parameters' con properties vacío → se omite si no hay propiedades."""
    if not tools:
        return None
    decls = []
    for t in tools:
        fn = t.get("function", t)
        params = fn.get("parameters") or {}
        decl = {"name": fn.get("name"), "description": fn.get("description", "")}
        if (params.get("properties") or {}):
            decl["parameters"] = params
        decls.append(decl)
    return [{"function_declarations": decls}]


def _to_gemini_contents(messages: list[dict]) -> tuple[str | None, list]:
    """messages estilo Ollama -> (system_instruction, contents de Gemini).
    Roles válidos en Gemini: 'user' y 'model'. El functionResponse va como 'user'."""
    system_txt = None
    contents: list[dict] = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            system_txt = m.get("content") or system_txt
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": m.get("content", "") or ""}]})
        elif role == "assistant":
            parts = []
            for c in (m.get("tool_calls") or []):
                fn = c.get("function", {}) or {}
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try: args = json.loads(args)
                    except Exception: args = {}
                part = {"functionCall": {"name": fn.get("name"), "args": args or {}}}
                # Gemini 3.x exige reenviar la firma de pensamiento del functionCall.
                if c.get("_tsig"):
                    part["thoughtSignature"] = c["_tsig"]
                parts.append(part)
            if m.get("content"):
                parts.append({"text": m["content"]})
            contents.append({"role": "model", "parts": parts or [{"text": ""}]})
        elif role == "tool":
            try:
                resp = json.loads(m.get("content", "{}"))
            except Exception:
                resp = {"result": m.get("content", "")}
            if not isinstance(resp, dict):
                resp = {"result": resp}
            contents.append({"role": "user", "parts": [{"functionResponse": {
                "name": m.get("name", "tool"), "response": resp}}]})
    return system_txt, contents


def _gemini_once(model: str, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        f"{GEMINI_URL}/{model}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _chat_gemini(messages: list[dict], tools=None, timeout: float = 45.0) -> dict:
    if not GEMINI_API_KEY:
        raise OSError("Falta GEMINI_API_KEY en el entorno.")
    system_txt, contents = _to_gemini_contents(messages)
    # thinkingBudget=0 → sin "pensamiento": respuesta rápida y barata (ideal por voz).
    body: dict = {"contents": contents,
                  "generationConfig": {"temperature": 0.3,
                                       "thinkingConfig": {"thinkingBudget": 0}}}
    if system_txt:
        body["system_instruction"] = {"parts": [{"text": system_txt}]}
    gtools = _gemini_tools(tools)
    if gtools:
        body["tools"] = gtools
    # Reintenta en el modelo principal y cae a los de respaldo si está saturado (503/429).
    data = None
    last_err: Exception | None = None
    for model in [GEMINI_MODEL, *GEMINI_FALLBACKS]:
        for _ in range(2):
            try:
                data = _gemini_once(model, body, timeout)
                break
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (429, 500, 503):
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = e
                continue
        if data is not None:
            break
    if data is None:
        raise last_err or OSError("Gemini no disponible")
    # Normalizar la respuesta de Gemini -> formato Ollama {"message": {...}}
    cands = data.get("candidates") or []
    text_parts, tool_calls = [], []
    if cands:
        for p in (cands[0].get("content", {}) or {}).get("parts", []) or []:
            if "functionCall" in p:
                fc = p["functionCall"]
                tc = {"function": {"name": fc.get("name"),
                                   "arguments": fc.get("args", {}) or {}}}
                if p.get("thoughtSignature"):   # requerido por Gemini 3.x al reenviar
                    tc["_tsig"] = p["thoughtSignature"]
                tool_calls.append(tc)
            elif "text" in p:
                text_parts.append(p["text"])
    msg: dict = {"role": "assistant", "content": "".join(text_parts)}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"message": msg}


# ---------------------------------------------------------------------------
# Bucle AGÉNTICO: razonar → (decidir herramienta → ejecutar → observar)* → responder
# ---------------------------------------------------------------------------
def responder(pregunta: str, idioma: str = "es", nivel: str = "sencillo",
              contexto: dict | None = None, max_steps: int = 3) -> dict:
    system = _system_prompt(idioma, nivel)

    # El agente SIEMPRE conoce la hora local (no tiene que preguntarla).
    t = (contexto or {}).get("tiempo")
    if isinstance(t, dict) and t.get("hora") is not None:
        try:
            es, en = _parte_del_dia(int(t["hora"]))
            parte = en if idioma == "en" else es
            etq = "Current local date/time" if idioma == "en" else "Fecha/hora local actual"
            system += f"\n{etq}: {t.get('fecha','')} {t.get('hhmm','')} ({parte})."
        except (TypeError, ValueError):
            pass

    # Narración DIRECTA (sin loop de herramientas) cuando el frontend ya pasó los datos
    # del polígono analizado → respuesta determinista y fiable.
    if contexto and isinstance(contexto.get("stats_cambio"), dict):
        datos = json.dumps(contexto["stats_cambio"], ensure_ascii=False)
        etq = "NISAR analysis data for the user's area" if idioma == "en" else "Datos del análisis NISAR de la zona del usuario"
        guia = (
            "Report the hazard(s) the NUMBERS actually show, not only landslides: "
            "if 'inundacion' has significant new water (agua_nueva_km2 or pct_zona_inundada) → report RIVER FLOODING; "
            "if 'deformacion' shows movement (mm/week) → report SLOW SLOPE MOVEMENT; "
            "if the backscatter change is significant → report a possible LANDSLIDE. "
            "Name the most relevant one(s) from the data and say what to do."
            if idioma == "en" else
            "Reporta el/los peligro(s) que REALMENTE muestran los números, no solo deslizamientos: "
            "si 'inundacion' tiene agua nueva significativa (agua_nueva_km2 o pct_zona_inundada) → reporta CRECIDA/INUNDACIÓN del río; "
            "si 'deformacion' muestra movimiento (mm/semana) → reporta MOVIMIENTO LENTO de ladera; "
            "si el cambio de retrodispersión es significativo → reporta posible DESLIZAMIENTO. "
            "Nombra el/los más relevante(s) según el dato y di qué hacer."
        )
        prompt = f"{pregunta}\n\n{etq}:\n{datos}\n\n{guia}"
        try:
            data = _chat([{"role": "system", "content": system},
                          {"role": "user", "content": prompt}], tools=None)
            return {"respuesta": (data.get("message", {}).get("content") or "").strip(),
                    "model": MODEL, "herramientas": ["datos_en_vivo"]}
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {"respuesta": None, "error": f"LLM no disponible: {e}", "model": MODEL}

    # El tool-calling del modelo local a veces falla y "filtra" una llamada corrupta
    # como texto (ej. "CallCheck…"). Reintentamos hasta 3 veces si pasa eso.
    def _garbled(t):
        t = (t or "").strip()
        return (not t) or t.startswith("Call") or "CallCheck" in t or "assistant<" in t
    try:
        for intento in range(3):
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": pregunta}]
            pasos = []; accion = None
            for _ in range(max_steps):
                data = _chat(messages, tools=TOOLS)
                msg = data.get("message", {}) or {}
                calls = msg.get("tool_calls")
                if not calls:
                    txt = (msg.get("content") or "").strip()
                    if _garbled(txt) and intento < 2:
                        break  # respuesta corrupta → reintentar desde cero
                    return {"respuesta": txt, "model": MODEL, "herramientas": pasos, "accion": accion}
                messages.append(msg)
                for c in calls:
                    fn = c.get("function", {}) or {}
                    name = fn.get("name", "")
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try: args = json.loads(args)
                        except Exception: args = {}
                    if name == "analizar_mi_zona":
                        try: km = float(args.get("km") or 1)
                        except Exception: km = 1.0
                        km = max(0.05, min(20.0, km))
                        accion = {"tipo": "analizar", "km": km}
                        result = {"ok": True, "km": km,
                                  "mensaje": f"Iniciando el análisis a {km} km alrededor del usuario."}
                    else:
                        result = _run_tool(name, args, contexto)
                    pasos.append(name)
                    messages.append({"role": "tool", "name": name,
                                     "content": json.dumps(result, ensure_ascii=False)})
            else:
                data = _chat(messages, tools=None)
                txt = (data.get("message", {}).get("content") or "").strip()
                if not _garbled(txt) or intento == 2:
                    return {"respuesta": txt, "model": MODEL, "herramientas": pasos, "accion": accion}
        return {"respuesta": txt, "model": MODEL, "herramientas": pasos, "accion": accion}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"respuesta": None, "error": f"LLM no disponible: {e}", "model": MODEL}


if __name__ == "__main__":
    ctx = {"zona": "Huánuco, carretera a Tingo María"}
    for idi, niv, q in [("es", "sencillo", "¿hay peligro en mi ruta?"),
                        ("en", "tecnico", "how severe is the change?"),
                        ("es", "sencillo", "hola, quién eres?")]:
        print(f"\n===== {idi}/{niv} :: {q} =====")
        out = responder(q, idioma=idi, nivel=niv, contexto=ctx)
        print("herramientas usadas:", out.get("herramientas"))
        print(out.get("respuesta") or out.get("error"))
