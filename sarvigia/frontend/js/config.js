// SARvigía — configuración del frontend
window.SARVIGIA_CONFIG = {
  // Base del backend. Vacío = usa el mismo host (ej. /api en producción).
  // En producción detrás de nginx: "/api"
  API_BASE: "/api",

  // Búsqueda/descarga reales vía backend. (La visualización de resultados
  // sigue en demo hasta que exista el módulo de procesamiento.)
  DEMO_MODE: false,

  // Vista inicial del mapa (valle de Huánuco)
  MAP_CENTER: [-76.242, -9.930],
  MAP_ZOOM: 11.2,

  // Atribución de tiles base
  OSM_TILES: [
    "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
  ],

  // Mapa base: solo OSM (las imágenes NASA GIBS se veían borrosas/estáticas al acercar).
  DEFAULT_BASE: "osm",
  BASEMAPS: {
    osm: {
      label: "🗺️ Calles",
      tiles: [
        "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
      ],
      maxzoom: 19, attribution: "© OpenStreetMap", labels: false
    }
  }
};
