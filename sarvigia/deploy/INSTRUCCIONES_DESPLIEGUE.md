# SARvigía — último paso de despliegue (requiere sudo)

Ya está hecho automáticamente:
- ✅ Contenedor `sarvigia-frontend` corriendo en `127.0.0.1:8101`
- ✅ DNS `sarvigia.thecreatorcampus.ai` creado (CNAME → tu túnel)

Falta **1 paso** que necesita tu contraseña (editar `/etc/cloudflared/config.yml`).
Copia y pega estos comandos en tu terminal (o aquí con el prefijo `!`):

```bash
# 1) Respaldo de la config actual
sudo cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.bak-sarvigia

# 2) Insertar la regla de SARvigía ANTES del catch-all 404
sudo sed -i 's#^  - service: http_status:404#  - hostname: sarvigia.thecreatorcampus.ai\n    service: http://localhost:8101\n  - service: http_status:404#' /etc/cloudflared/config.yml

# 3) Verificar que quedó bien (debe aparecer el bloque sarvigia antes del 404)
sudo cat /etc/cloudflared/config.yml

# 4) Reiniciar el túnel
sudo systemctl restart cloudflared
```

Después de esto, abre: **https://sarvigia.thecreatorcampus.ai**

## Bloque que se inserta (referencia)
```yaml
  - hostname: sarvigia.thecreatorcampus.ai
    service: http://localhost:8101
```

## Si algo sale mal (revertir)
```bash
sudo cp /etc/cloudflared/config.yml.bak-sarvigia /etc/cloudflared/config.yml
sudo systemctl restart cloudflared
```
Tus cursos (`aula` y landing) no se tocan en ningún momento.
