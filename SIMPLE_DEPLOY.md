# Simple Deploy - Servidor con Pocos Recursos

## Setup (Uvicorn + Docker + Reverse Proxy)

### Arquitectura
```
Tu Reverse Proxy (Nginx/Caddy/Traefik)
    ↓
  Docker Container (Uvicorn single process)
    ↓
  FastAPI App
```

**Ventajas:**
- Bajo consumo de memoria (~500MB)
- Simple de mantener
- Escalable horizontalmente si creces

## Deploy Rápido

### 1. Setup Environment
```bash
cp .env.production.example .env.production
nano .env.production
```

Edita solo lo necesario:
```bash
KICK_CHANNEL=tu_canal
ENABLE_REDIS_CACHE=false  # opcional, ahorra recursos
```

### 2. Build & Run
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Verify
```bash
curl http://localhost:8000/health
```

## Reverse Proxy Config

### Nginx (Recomendado)
```nginx
# /etc/nginx/sites-available/kick-tts

upstream kick_tts {
    server localhost:8000;
}

server {
    listen 80;
    server_name tu-dominio.com;

    # WebSocket
    location /events {
        proxy_pass http://kick_tts;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Static files (optional, sirve directo)
    location /static/ {
        alias /ruta/a/tts-chat/static/;
        expires 1d;
    }

    # Rest of app
    location / {
        proxy_pass http://kick_tts;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Activar:
```bash
ln -s /etc/nginx/sites-available/kick-tts /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Caddy (Más Simple)
```caddy
# Caddyfile
tu-dominio.com {
    reverse_proxy localhost:8000
}
```

Caddy maneja SSL automático con Let's Encrypt.

### Traefik (Docker Labels)
```yaml
# En docker-compose.prod.yml, añade labels:
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.kick-tts.rule=Host(`tu-dominio.com`)"
  - "traefik.http.routers.kick-tts.entrypoints=websecure"
  - "traefik.http.routers.kick-tts.tls.certresolver=letsencrypt"
```

## Recursos del Servidor

### Mínimo Requerido
- **RAM:** 512MB (1GB recomendado)
- **CPU:** 1 vCore
- **Disk:** 2GB
- **Network:** 10Mbps

### Consumo Real
```bash
docker stats kick-tts-bot

# Ejemplo:
# NAME            CPU %    MEM USAGE / LIMIT
# kick-tts-bot    2-5%     350MB / 1GB
# kick-tts-redis  0.1%     15MB / 512MB
```

### Optimizaciones para Recursos Bajos

#### Deshabilitar Redis
```bash
# .env.production
ENABLE_REDIS_CACHE=false
```
Ahorra ~30MB RAM, pero pierdes cache de TTS.

#### Reducir Cache de Audio
```bash
# Limpiar audios viejos cada día
0 2 * * * find /ruta/static/audio -type f -mtime +1 -delete
```

#### Limitar Tamaño de Mensajes
```bash
# .env.production
MAX_MESSAGE_LENGTH=100  # Reduce de 200 a 100
```

## Escalar si Crece el Canal

### Opción 1: Upgrade Servidor
Cambiar a plan con más recursos.

### Opción 2: Escalar Horizontalmente
```bash
# Múltiples contenedores
docker-compose -f docker-compose.prod.yml up -d --scale tts-bot=3
```

Nginx upstream:
```nginx
upstream kick_tts {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

### Opción 3: Separar Componentes
- Servidor 1: App
- Servidor 2: Redis (si usas cache)

## Monitoreo Simple

### Health Check
```bash
# /etc/cron.d/kick-tts-health
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart kick-tts
```

### Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f --tail=50 tts-bot
```

### Disk Space
```bash
du -sh static/audio static/cache
```

## Troubleshooting

### Container Crashea
```bash
# Ver logs
docker logs kick-tts-bot --tail=100

# Restart
docker-compose -f docker-compose.prod.yml restart tts-bot
```

### Sin Memoria
```bash
# Check
free -h

# Agregar swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Audio No Se Genera
```bash
# Check Piper model
docker exec -it kick-tts-bot ls -lh models/

# Re-download si falta
docker-compose -f docker-compose.prod.yml build --no-cache
```

## Providers Baratos Recomendados

### VPS (Virtual Private Server)
- **Contabo:** €4/mes (1 vCore, 4GB RAM) - Alemania
- **Hetzner:** €4.5/mes (1 vCore, 2GB RAM) - Alemania
- **DigitalOcean:** $6/mes (1 vCore, 1GB RAM) - Global
- **Linode:** $5/mes (1 vCore, 1GB RAM) - Global
- **Vultr:** $5/mes (1 vCore, 1GB RAM) - Global

### PaaS (Platform as a Service)
- **Railway:** $5/mes (512MB RAM incluido)
- **Render:** $7/mes (512MB RAM)
- **Fly.io:** Free tier (256MB RAM) - Suficiente para empezar

### Recomendación
Si es tu primer deploy y el canal es pequeño:
1. **Fly.io** (free tier) o **Railway** (trial)
2. Cuando crezcas, VPS de **Contabo** (mejor precio/calidad)

## Quick Commands

```bash
# Start
docker-compose -f docker-compose.prod.yml up -d

# Stop
docker-compose -f docker-compose.prod.yml down

# Restart
docker-compose -f docker-compose.prod.yml restart

# Logs
docker-compose -f docker-compose.prod.yml logs -f tts-bot

# Update code
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats
```

## SSL/HTTPS

### Opción 1: Certbot (Nginx)
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d tu-dominio.com
```

### Opción 2: Caddy (Automático)
Caddy maneja SSL automáticamente, zero config.

### Opción 3: Cloudflare (Gratis)
1. Dominio en Cloudflare
2. Proxy enabled (orange cloud)
3. SSL mode: Flexible
4. Listo, HTTPS gratis sin configurar nada

## Backup

```bash
# Backup sounds
tar -czf backup-sounds-$(date +%Y%m%d).tar.gz static/sounds/

# Backup .env
cp .env.production .env.production.backup

# Restore
tar -xzf backup-sounds-20240130.tar.gz
```

## Summary

**Tu setup ideal:**
```
Cloudflare (SSL gratis)
    ↓
Nginx/Caddy (reverse proxy en VPS)
    ↓
Docker (1 contenedor Uvicorn)
    ↓
FastAPI App
```

**Costo mensual:** ~$5 VPS
**Tiempo deploy:** ~15 minutos
**Mantenimiento:** Mínimo
