# Desplegar Qaway en la nube (Oracle Always Free + Cloudflare Tunnel)

Objetivo: que `https://qaway.thecreatorcampus.ai` funcione **sin tu PC encendida**.
Costo: **~$0** (Oracle Always Free ARM + tu API key de Gemini).

El demo por voz lee los JSON de `backend/static/` → responde al instante **sin GPU ni
descargas**. Por eso la VM solo necesita CPU/RAM normales.

---

## 1) Crear la VM en Oracle Cloud (una vez)

1. Entra a https://cloud.oracle.com → crea cuenta (o inicia sesión).
2. **Compute → Instances → Create instance**:
   - **Shape:** cambia a *Ampere* → **VM.Standard.A1.Flex**, pon **2 OCPU / 12 GB** (dentro del Always Free; puedes subir a 4/24).
   - **Image:** Ubuntu 22.04 (ARM).
   - **Networking:** crea/usa una VCN con subred pública.
   - **SSH keys:** sube tu clave pública (`~/.ssh/id_*.pub`) o deja que genere una y descárgala.
   - Create.
   > ⚠️ Si sale **"Out of host capacity"** (común en ARM free): reintenta en otra
   > *Availability Domain*, o cambia de región. Si insiste, usa el plan B (Hetzner, abajo).
3. Cuando esté *Running*, copia la **IP pública**.

### Abrir el firewall de Oracle (solo salida/HTTP interno no hace falta públicamente)
Cloudflare Tunnel sale **hacia afuera**, así que **no necesitas abrir puertos de entrada**.
Solo asegúrate de permitir salida (por defecto está abierta). No toques los Security Lists.

---

## 2) Entrar y preparar la VM

```bash
ssh ubuntu@TU_IP_PUBLICA     # (usuario 'ubuntu' en imágenes Ubuntu)

# Docker + compose
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && newgrp docker

# Clonar el repo público
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/louis9RM/qaway.git
cd qaway/sarvigia/deploy
```

## 3) Configurar la clave de Gemini

```bash
cp .env.example .env
nano .env        # pega tu GEMINI_API_KEY (la de ~/robotica-remota/portal-datos/gemini.key)
```

## 4) Levantar Qaway (build ARM, ~5-10 min la 1ª vez)

```bash
docker compose -f docker-compose.cloud.yml up -d --build

# Verificar
curl -s http://127.0.0.1:8100/api/health        # → {"ok":true,"service":"qaway-backend"}
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8101/   # → 200
```

Prueba el agente directo (debe narrar con datos de Huánuco):
```bash
curl -s -X POST http://127.0.0.1:8100/api/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿hay peligro en mi ruta?","idioma":"es","nivel":"sencillo","contexto":{"zona":"Huánuco"}}'
```

## 5) Cloudflare Tunnel en la VM → dominio público

```bash
# Instalar cloudflared (ARM64)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
sudo mv cloudflared /usr/local/bin/ && sudo chmod +x /usr/local/bin/cloudflared

cloudflared tunnel login                 # abre un link; autoriza thecreatorcampus.ai
cloudflared tunnel create qaway-vm       # crea el túnel (guarda el ID y el credentials.json)

# Enrutar el subdominio al túnel de la VM (repunta el CNAME; tu PC deja de servir esta URL)
cloudflared tunnel route dns qaway-vm qaway.thecreatorcampus.ai
```

Crea el config `~/.cloudflared/config.yml`:
```yaml
tunnel: qaway-vm
credentials-file: /home/ubuntu/.cloudflared/<ID-DEL-TUNEL>.json
ingress:
  - hostname: qaway.thecreatorcampus.ai
    service: http://127.0.0.1:8101
  - service: http_status:404
```

Correrlo como servicio (sobrevive reinicios):
```bash
sudo cloudflared --config /home/ubuntu/.cloudflared/config.yml service install
sudo systemctl enable --now cloudflared
```

## 6) Verificar desde internet
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://qaway.thecreatorcampus.ai   # → 200
```
Abre la URL en el celular, prueba la voz. ✅ Ya no depende de tu PC.

---

## Plan B (si Oracle no da capacidad): Hetzner ~$15
Idéntico desde el paso 2, pero x86 (sin líos de ARM):
1. https://console.hetzner.cloud → Add Server → **CPX31** (4 vCPU/8GB/160GB), Ubuntu 22.04.
2. Sigue pasos 2–6 igual, pero en el paso 5 usa `cloudflared-linux-amd64` en vez de `-arm64`.

## Notas
- El frontend apunta al backend por ruta relativa `/api` (nginx hace proxy) → no hay que
  cambiar URLs al mover de dominio.
- El demo por voz NO descarga nada (usa los JSON de static). El análisis por polígono sí
  descarga de ASF en la VM (lento, 4-15 min) — opcional para el jurado.
- Para actualizar: `git pull && docker compose -f docker-compose.cloud.yml up -d --build`.
