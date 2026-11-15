# SARvigía — Frontend

Sitio estático responsive (compu / tablet / celular) con mapa real **MapLibre GL**.
Muestra zonas monitoreadas, dibujo de polígono, capas SAR, línea de tiempo y semáforo de riesgo.

> Estado: el mapa, navegación, selección de zona, dibujo de polígono, línea de tiempo y
> diseño son **reales**. Las **capas SAR están en modo demostración** hasta conectar el
> backend; se activan poniendo `DEMO_MODE:false` en `js/config.js` (consume `/api`).

## Estructura
```
frontend/
├── index.html        # página principal
├── css/styles.css    # estilos + temas claro/oscuro
├── js/config.js      # API_BASE, DEMO_MODE, centro del mapa  ← editable
├── js/app.js         # mapa, capas, UI, conexión /api
└── prototipo.html    # prototipo previo (referencia, no se despliega)
```

## Probar localmente
```bash
cd frontend
python3 -m http.server 8088
# abrir http://localhost:8088
```

## Desplegar (nginx estático, subdominio)
Servir la carpeta `frontend/` y enrutar `/api` al backend. Ejemplo de server block:
```nginx
server {
    listen 80;
    server_name sarvigia.thecreatorcampus.ai;

    root /home/ever/robotica-remota/spaceapps/sarvigia/frontend;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }

    location /api/ {
        proxy_pass http://127.0.0.1:8100/;   # backend SARvigía (futuro)
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```
Luego crear el registro DNS `sarvigia` apuntando al servidor (TLS vía Cloudflare).

## Dependencias (CDN)
- MapLibre GL JS 4.7.1 (cdnjs)
- Google Fonts (Space Grotesk, Inter, IBM Plex Mono)
- Tiles base: OpenStreetMap (gratis; para producción con tráfico, usar un proveedor propio).
