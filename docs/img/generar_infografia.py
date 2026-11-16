import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def create_infographic():
    fig = plt.figure(figsize=(24, 13.5), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 2400)
    ax.set_ylim(0, 1350)
    ax.axis('off')

    # Background
    bg = patches.Rectangle((0, 0), 2400, 1350, facecolor='#0B132B')
    ax.add_patch(bg)

    # Header Banner
    header_box = FancyBboxPatch((60, 1220), 2280, 95, boxstyle="round,pad=10,rounding_size=15",
                                facecolor='#1C2541', edgecolor='#3A506B', linewidth=2)
    ax.add_patch(header_box)

    ax.text(90, 1275, "QAWAY (El que vigila) — Arquitectura y Pipeline Operativo End-to-End",
            fontsize=26, fontweight='bold', color='#FFFFFF', family='DejaVu Sans')
    ax.text(90, 1240, "NASA Space Apps Challenge 2026 · Reto: Dancing with the SARs (NISAR) · Transformación de Radar Satelital en Alertas por Voz",
            fontsize=15, color='#00F5D4', family='DejaVu Sans')

    badge = FancyBboxPatch((2000, 1240), 320, 50, boxstyle="round,pad=5,rounding_size=10",
                           facecolor='#00F5D4', edgecolor='none')
    ax.add_patch(badge)
    ax.text(2160, 1265, "100% OPEN SCIENCE", fontsize=13, fontweight='bold', color='#0B132B',
            family='DejaVu Sans', ha='center', va='center')

    # ================= STAGE 1: ENTRADAS (Col 1: x: 60 - 580) =================
    s1_box = FancyBboxPatch((60, 260), 520, 920, boxstyle="round,pad=10,rounding_size=18",
                            facecolor='#162238', edgecolor='#3A506B', linewidth=1.5)
    ax.add_patch(s1_box)

    # Title Stage 1
    ax.text(90, 1140, "1. CAPTURA Y MODALIDADES", fontsize=20, fontweight='bold', color='#FFB703', family='DejaVu Sans')
    ax.text(90, 1110, "Definición del área de interés geográfica", fontsize=13, color='#A0AEC0', family='DejaVu Sans')

    # Card 1A: Modo Conductor
    c1a = FancyBboxPatch((85, 710), 470, 360, boxstyle="round,pad=8,rounding_size=12",
                         facecolor='#1F2F4A', edgecolor='#FB8500', linewidth=2)
    ax.add_patch(c1a)
    ax.text(110, 1030, "MODO CONDUCTOR (Manos Libres)", fontsize=16, fontweight='bold', color='#FB8500', family='DejaVu Sans')
    ax.text(110, 995, "• Consulta por voz en lenguaje natural:\n  '¿Mi ruta está despejada de peligro?'", fontsize=13, color='#E2E8F0', family='DejaVu Sans')
    ax.text(110, 925, "• Geolocalización GPS automática del vehículo.", fontsize=13, color='#E2E8F0', family='DejaVu Sans')
    ax.text(110, 875, "• Trazado dinámico de búfer de carretera\n  (OpenStreetMap / Overpass API + Turf.js).", fontsize=13, color='#E2E8F0', family='DejaVu Sans')
    ax.text(110, 800, "• Objetivo: Cero distracción visual al volante\n  en curvas andinas peligrosas.", fontsize=13, fontstyle='italic', color='#CBD5E1', family='DejaVu Sans')

    pill1a = FancyBboxPatch((110, 730), 220, 36, boxstyle="round,pad=3,rounding_size=8", facecolor='#FB8500', edgecolor='none')
    ax.add_patch(pill1a)
    ax.text(220, 748, "Prioridad: Seguridad Vial", fontsize=11, fontweight='bold', color='#0B132B', ha='center', va='center')

    # Card 1B: Modo Analista
    c1b = FancyBboxPatch((85, 300), 470, 370, boxstyle="round,pad=8,rounding_size=12",
                         facecolor='#1F2F4A', edgecolor='#00F5D4', linewidth=1.5)
    ax.add_patch(c1b)
    ax.text(110, 630, "MODO ANALISTA (Especialista)", fontsize=16, fontweight='bold', color='#00F5D4', family='DejaVu Sans')
    ax.text(110, 595, "• Trazado de polígonos interactivo en mapa.", fontsize=13, color='#E2E8F0', family='DejaVu Sans')
    ax.text(110, 550, "• Focalizado en laderas inestables específicas,\n  quebradas críticas o infraestructura de puentes.", fontsize=13, color='#E2E8F0', family='DejaVu Sans')
    ax.text(110, 475, "• Selección temporal de órbitas de satélite.", fontsize=13, color='#E2E8F0', family='DejaVu Sans')
    ax.text(110, 425, "• Enfoque técnico para entidades viales\n  (Provías Nacional, MTC, INDECI).", fontsize=13, fontstyle='italic', color='#CBD5E1', family='DejaVu Sans')

    pill1b = FancyBboxPatch((110, 330), 220, 36, boxstyle="round,pad=3,rounding_size=8", facecolor='#00F5D4', edgecolor='none')
    ax.add_patch(pill1b)
    ax.text(220, 348, "Rigor Estadístico", fontsize=11, fontweight='bold', color='#0B132B', ha='center', va='center')

    # ================= STAGE 2: INGESTA SATELITAL (Col 2: x: 640 - 1160) =================
    s2_box = FancyBboxPatch((640, 260), 520, 920, boxstyle="round,pad=10,rounding_size=18",
                            facecolor='#162238', edgecolor='#3A506B', linewidth=1.5)
    ax.add_patch(s2_box)

    ax.text(670, 1140, "2. INGESTA Y DATOS ESPACIALES", fontsize=20, fontweight='bold', color='#FFB703', family='DejaVu Sans')
    ax.text(670, 1110, "Búsqueda y descarga automatizada ASF bajo demanda", fontsize=13, color='#A0AEC0', family='DejaVu Sans')

    # Card 2A: NISAR GCOV
    c2a = FancyBboxPatch((665, 870), 470, 200, boxstyle="round,pad=8,rounding_size=12",
                         facecolor='#1F2F4A', edgecolor='#38BDF8', linewidth=1.5)
    ax.add_patch(c2a)
    ax.text(690, 1030, "NISAR GCOV (Banda L)", fontsize=16, fontweight='bold', color='#38BDF8', family='DejaVu Sans')
    ax.text(690, 995, "• Retrodispersión calibrada radiométricamente (dB).", fontsize=13, color='#E2E8F0')
    ax.text(690, 960, "• Polarizaciones cruzadas (HH / HV).", fontsize=13, color='#E2E8F0')
    ax.text(690, 925, "• Penetración a través de nubes, lluvia y follaje.", fontsize=13, color='#E2E8F0')
    ax.text(690, 890, "• Formato HDF5 descargado vía ASF Search API.", fontsize=12, color='#94A3B8')

    # Card 2B: NISAR GUNW
    c2b = FancyBboxPatch((665, 630), 470, 210, boxstyle="round,pad=8,rounding_size=12",
                         facecolor='#1F2F4A', edgecolor='#38BDF8', linewidth=1.5)
    ax.add_patch(c2b)
    ax.text(690, 800, "NISAR GUNW (Interferometría)", fontsize=16, fontweight='bold', color='#38BDF8', family='DejaVu Sans')
    ax.text(690, 765, "• Fase interferométrica desenvuelta (Unwrapped Phase).", fontsize=13, color='#E2E8F0')
    ax.text(690, 730, "• Coherencia interferométrica temporal (0 a 1).", fontsize=13, color='#E2E8F0')
    ax.text(690, 695, "• Medición de deformación en línea de visión (LOS).", fontsize=13, color='#E2E8F0')
    ax.text(690, 650, "• Cobertura completa sobre territorio peruano.", fontsize=12, color='#94A3B8')

    # Card 2C: Copernicus DEM
    c2c = FancyBboxPatch((665, 300), 470, 290, boxstyle="round,pad=8,rounding_size=12",
                         facecolor='#1F2F4A', edgecolor='#38BDF8', linewidth=1.5)
    ax.add_patch(c2c)
    ax.text(690, 550, "Copernicus GLO-30 DEM", fontsize=16, fontweight='bold', color='#38BDF8', family='DejaVu Sans')
    ax.text(690, 510, "• Modelo Digital de Elevación (resolución 30 m).", fontsize=13, color='#E2E8F0')
    ax.text(690, 465, "• Cálculo matricial de pendiente topográfica (grados).", fontsize=13, color='#E2E8F0')
    ax.text(690, 420, "• Identificación de umbrales críticos de inestabilidad\n  (laderas > 25° y 35° de inclinación).", fontsize=13, color='#E2E8F0')
    ax.text(690, 345, "• Factor de cruce y ponderación en riesgo de ladera.", fontsize=12, color='#94A3B8')

    # ================= STAGE 3: MOTOR SAR (Col 3: x: 1220 - 1740) =================
    s3_box = FancyBboxPatch((1220, 260), 520, 920, boxstyle="round,pad=10,rounding_size=18",
                            facecolor='#162238', edgecolor='#3A506B', linewidth=1.5)
    ax.add_patch(s3_box)

    ax.text(1250, 1140, "3. MOTOR DE PROCESAMIENTO SAR", fontsize=20, fontweight='bold', color='#FFB703', family='DejaVu Sans')
    ax.text(1250, 1110, "Algoritmos científicos cuantitativos (Python / NumPy / Rasterio)", fontsize=13, color='#A0AEC0', family='DejaVu Sans')

    # Mod 1: Deslizamiento
    m1 = FancyBboxPatch((1245, 930), 470, 155, boxstyle="round,pad=8,rounding_size=12",
                        facecolor='#1F2F4A', edgecolor='#E63946', linewidth=1.5)
    ax.add_patch(m1)
    ax.text(1265, 1050, "Deslizamientos y Colapsos", fontsize=15, fontweight='bold', color='#E63946')
    ax.text(1265, 1015, "• Detección de cambio Log-Ratio en dB.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 985, "• Test de Wishart/Conradsen para polarimetría.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 950, "• Identifica rotura de vegetación y suelo expuesto.", fontsize=12, color='#94A3B8')

    # Mod 2: Deformacion InSAR
    m2 = FancyBboxPatch((1245, 740), 470, 165, boxstyle="round,pad=8,rounding_size=12",
                        facecolor='#1F2F4A', edgecolor='#F4A261', linewidth=1.5)
    ax.add_patch(m2)
    ax.text(1265, 870, "Deformación Lenta InSAR (Alerta Temprana)", fontsize=15, fontweight='bold', color='#F4A261')
    ax.text(1265, 835, "• Conversión de fase desenvuelta a mm/semana.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 805, "• Detecta reptación antes del colapso catastrófico.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 765, "• Valida el White Paper de Landslides de NASA/JPL.", fontsize=12, color='#94A3B8')

    # Mod 3: Inundacion
    m3 = FancyBboxPatch((1245, 530), 470, 185, boxstyle="round,pad=8,rounding_size=12",
                        facecolor='#1F2F4A', edgecolor='#48CAE4', linewidth=1.5)
    ax.add_patch(m3)
    ax.text(1265, 680, "Inundación y Desborde de Ríos", fontsize=15, fontweight='bold', color='#48CAE4')
    ax.text(1265, 645, "• Metodología validada por NASA ARSET.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 615, "• Umbralización bimodal adaptativa de Otsu.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 580, "• Detección de agua nueva sobre la plataforma vial.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 545, "• Filtro morfológico para remover falsos positivos.", fontsize=12, color='#94A3B8')

    # Mod 4: Fusión y Coherencia
    m4 = FancyBboxPatch((1245, 300), 470, 205, boxstyle="round,pad=8,rounding_size=12",
                        facecolor='#1F2F4A', edgecolor='#2A9D8F', linewidth=1.5)
    ax.add_patch(m4)
    ax.text(1265, 470, "Coherencia y Matriz de Riesgo", fontsize=15, fontweight='bold', color='#2A9D8F')
    ax.text(1265, 435, "• Coherencia interferométrica temporal (0 a 1).", fontsize=12, color='#E2E8F0')
    ax.text(1265, 400, "• Fusión multidimensional: Cambio + InSAR + DEM.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 365, "• Veredicto ponderado: BAJO · MODERADO · ALTO.", fontsize=12, color='#E2E8F0')
    ax.text(1265, 325, "• Cálculo de área superficial afectada en m² / hectáreas.", fontsize=12, color='#94A3B8')

    # ================= STAGE 4: AGENTE IA Y SALIDA (Col 4: x: 1800 - 2340) =================
    s4_box = FancyBboxPatch((1800, 260), 540, 920, boxstyle="round,pad=10,rounding_size=18",
                            facecolor='#162238', edgecolor='#3A506B', linewidth=1.5)
    ax.add_patch(s4_box)

    ax.text(1830, 1140, "4. AGENTE IA Y SALIDAS", fontsize=20, fontweight='bold', color='#FFB703', family='DejaVu Sans')
    ax.text(1830, 1110, "Razonamiento con Tool-Calling y entrega adaptada", fontsize=13, color='#A0AEC0', family='DejaVu Sans')

    # Agente IA Box
    ag_box = FancyBboxPatch((1825, 750), 490, 320, boxstyle="round,pad=8,rounding_size=12",
                            facecolor='#1F2F4A', edgecolor='#9D4EDD', linewidth=2)
    ax.add_patch(ag_box)
    ax.text(1850, 1030, "AGENTE DE IA (Agentic Core)", fontsize=16, fontweight='bold', color='#D8B4FE')
    ax.text(1850, 995, "• Soporte dual de inferencia:", fontsize=13, color='#E2E8F0')
    ax.text(1870, 965, "- Google Gemini API (Gemini Flash en la nube)", fontsize=12, color='#A78BFA')
    ax.text(1870, 935, "- Modelo local Ollama / Qwen 2.5 (GPU)", fontsize=12, color='#A78BFA')
    ax.text(1850, 895, "• Tool-Calling autónomo con 7 herramientas SAR.", fontsize=13, color='#E2E8F0')
    ax.text(1850, 855, "• Evaluación de contexto vial y severidad de riesgo.", fontsize=13, color='#E2E8F0')
    ax.text(1850, 810, "• Adaptación de tono: ciudadano vs. técnico.", fontsize=13, color='#E2E8F0')
    ax.text(1850, 770, "• Retención de 'thoughtSignature' para Gemini 3.x.", fontsize=11, color='#94A3B8')

    # Output 1: Conductor
    out1 = FancyBboxPatch((1825, 520), 490, 205, boxstyle="round,pad=8,rounding_size=12",
                          facecolor='#1F2F4A', edgecolor='#FB8500', linewidth=2)
    ax.add_patch(out1)
    ax.text(1850, 690, "VOZ AL CONDUCTOR (Web Speech TTS)", fontsize=15, fontweight='bold', color='#FB8500')
    ax.text(1850, 650, "\"Alerta en km 441: ladera inestable detectada\n a 500 metros. Reduzca la velocidad.\"", fontsize=13, fontstyle='italic', color='#FFE8D6')
    ax.text(1850, 580, "• Síntesis de voz directa y sin jerga técnica.", fontsize=12, color='#E2E8F0')
    ax.text(1850, 545, "• Advertencia oportuna antes de llegar a la curva.", fontsize=12, color='#E2E8F0')

    # Output 2: Analista
    out2 = FancyBboxPatch((1825, 300), 490, 195, boxstyle="round,pad=8,rounding_size=12",
                          facecolor='#1F2F4A', edgecolor='#00F5D4', linewidth=1.5)
    ax.add_patch(out2)
    ax.text(1850, 460, "DASHBOARD TÉCNICO (Pantalla)", fontsize=15, fontweight='bold', color='#00F5D4')
    ax.text(1850, 420, "• Tablas estadísticas y distribución de pendiente.", fontsize=12, color='#E2E8F0')
    ax.text(1850, 385, "• Desplazamiento máximo y medio (mm/sem).", fontsize=12, color='#E2E8F0')
    ax.text(1850, 350, "• Exportación para Provías Nacional e INDECI.", fontsize=12, color='#E2E8F0')
    ax.text(1850, 315, "• Coherencia interferométrica y nivel de certeza.", fontsize=11, color='#94A3B8')

    # ================= CONECTORES / FLECHAS ENTRE ETAPAS =================
    arrow_props = dict(facecolor='#00F5D4', edgecolor='none', width=3, headwidth=14, headlength=14)
    # S1 -> S2
    ax.annotate('', xy=(635, 720), xytext=(585, 720), arrowprops=arrow_props)
    # S2 -> S3
    ax.annotate('', xy=(1215, 720), xytext=(1165, 720), arrowprops=arrow_props)
    # S3 -> S4
    ax.annotate('', xy=(1795, 720), xytext=(1745, 720), arrowprops=arrow_props)

    # Footer
    footer = FancyBboxPatch((60, 40), 2280, 180, boxstyle="round,pad=8,rounding_size=12",
                            facecolor='#162238', edgecolor='#3A506B', linewidth=1)
    ax.add_patch(footer)

    ax.text(90, 175, "CARACTERÍSTICAS TÉCNICAS CLAVE DEL SISTEMA:", fontsize=15, fontweight='bold', color='#FFB703')
    ax.text(90, 140, "• Procesamiento bajo demanda (FastAPI + Asf-Search): Descarga únicamente las escenas satelitales necesarias para el polígono de interés.", fontsize=13, color='#CBD5E1')
    ax.text(90, 110, "• Gestión de Caché LRU (100 GB): Optimiza el tiempo de respuesta reduciendo el análisis a segundos en tramos viales previamente consultados.", fontsize=13, color='#CBD5E1')
    ax.text(90, 80, "• Respaldo Oficial NASA: Métodos validados con los White Papers de Aplicaciones de NISAR (JPL/Caltech) y guías NASA ARSET para inundaciones.", fontsize=13, color='#CBD5E1')
    ax.text(90, 50, "• Mascota Qaway: Llama andina animada que humaniza y conecta la tecnología espacial con la identidad cultural del Perú.", fontsize=13, color='#CBD5E1')

    ax.text(2300, 50, "Team thecreator · NASA Space Apps 2026", fontsize=12, color='#64748B', ha='right')

    plt.tight_layout()
    output_path = 'docs/img/infografia_como_funciona.png'
    plt.savefig(output_path, facecolor='#0B132B', edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"Infografía generada exitosamente en: {output_path}")

if __name__ == '__main__':
    create_infographic()
