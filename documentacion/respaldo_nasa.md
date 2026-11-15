# Qaway — Respaldo oficial NASA (White Papers NISAR)

Fuente: *NISAR Applications White Papers* (JPL/Caltech–NASA, 2017), de la página
**NISAR Societal Benefits**. Estos documentos oficiales **validan el enfoque de Qaway**
y responden la pregunta del reto *"What future applications of NISAR are possible?"*.

---

## 1. El problema (cifras oficiales NASA)
- Los deslizamientos matan **entre 2000 y 3000 personas al año** en el mundo (Petley, 2017).
- Pueden ser **lentos** (una fracción de pulgada al año, activos por décadas, dañando carreteras y edificios) o **catastróficos** (decenas de km/h, pérdida de vidas e infraestructura).
- Ocurren en **laderas empinadas, durante o después de lluvias intensas** o por sismos.
  → **Valida que Qaway cruce pendiente (DEM) + lluvia como factores de riesgo.**

## 2. Cómo NISAR lo resuelve (validación del método de Qaway)
- NISAR mide el **movimiento del terreno directamente** mediante **interferometría SAR (InSAR)**: el interferograma muestra "contornos de movimiento del terreno".
  → **Es exactamente el módulo de deformación de Qaway (GUNW → mm).**
- Observa **de día/noche y con cualquier clima**, **4–6 veces al mes**, a **5–10 m** de resolución.
- Productos disponibles **1–2 días tras la observación** (horas ante desastres) → datos oportunos y accionables.

## 3. La aplicación futura (cita textual clave para el pitch)
> *"A regular schedule of radar imaging with NISAR … will enable **detection of slow-moving
> landslides, so damage can be avoided, and potentially provide forewarning of rapid landslides
> in the weeks to months prior to their catastrophic failure.**"* — NISAR Applications: Landslides (NASA/JPL)

→ **Esto ES la propuesta de Qaway: alerta temprana semanas/meses antes del derrumbe.**

## 4. Subsidencia / infraestructura (módulo futuro, respaldado)
- La subsidencia *"often goes unnoticed until the damage is done"* → carreteras y puentes deformados, inundaciones más frecuentes.
  → Respalda extender Qaway a **hundimiento de carreteras y represas** (ej. Chaglla).

---

## Mapeo: White Paper NASA ↔ función de Qaway
| Dice el White Paper NASA | Qaway lo implementa |
|---|---|
| InSAR mide movimiento del terreno | Módulo de deformación (GUNW → mm/semana) |
| Laderas empinadas + lluvia = riesgo | DEM pendiente (+ lluvia GPM, próximo) |
| Alerta semanas/meses antes del colapso | Alerta temprana por voz al conductor |
| Datos en horas ante desastres | Descarga + análisis bajo demanda |

## Nota técnica verificada (honesta)
- **OPERA DISP** (desplazamiento ya procesado) **solo cubre Norteamérica** (hasta Panamá) → **no aplica a Perú**; por eso Qaway calcula la deformación con el **GUNW** directamente.
- **OPERA DSWx** (agua, casi-global) → opción futura para el **módulo de inundaciones** (Tumbes).

## Referencias (APA)
NASA & ISRO. (2017). *NISAR Applications: Landslide hazards to infrastructure* [White paper]. Jet Propulsion Laboratory, California Institute of Technology. https://assets.science.nasa.gov/content/dam/science/missions/nisar/nisar-jpl/pdf/NISAR_Applications_Landslides.pdf

NASA & ISRO. (2017). *NISAR Applications: Subsidence and a sinking landscape* [White paper]. Jet Propulsion Laboratory, California Institute of Technology. https://assets.science.nasa.gov/content/dam/science/missions/nisar/nisar-jpl/pdf/NISAR_Applications_Subsidence.pdf
