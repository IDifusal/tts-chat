# Quick Deploy Guide

## Local Development
```bash
docker-compose up
```

## Production Deploy Options

### Simple (Servidor con Pocos Recursos)
**Recomendado para:** VPS barato, canal pequeño/mediano

```bash
# Setup
cp .env.production.example .env.production
nano .env.production  # KICK_CHANNEL=tu_canal

# Run
docker-compose -f docker-compose.simple.yml up -d

# Verify
curl http://localhost:8000/health
```

**Características:**
- Uvicorn single process (bajo consumo)
- Redis opcional
- ~500MB RAM
- Escala con tu reverse proxy

Ver: **SIMPLE_DEPLOY.md** para más detalles.

---

### Full Production (Servidor con Buenos Recursos)

### 1. Setup Environment
```bash
cp .env.production.example .env.production
nano .env.production  # Edit values
```

### 2. Build & Run
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Verify
```bash
curl http://localhost/health
```

### 4. View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f tts-bot
```

## SSL Setup (Let's Encrypt)

```bash
# Install certbot
apt install certbot

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Copy certs
mkdir ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/

# Update nginx.conf (uncomment SSL section)
# Restart
docker-compose -f docker-compose.prod.yml restart nginx
```

## Commands

### Restart (Zero Downtime)
```bash
docker-compose -f docker-compose.prod.yml exec tts-bot kill -HUP 1
```

### Update Code
```bash
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Scale Workers
```bash
WORKERS=17 docker-compose -f docker-compose.prod.yml up -d
```

### View Metrics
```bash
docker stats
```

## VPS Quick Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone repo
git clone <your-repo>
cd tts-chat

# Setup env
cp .env.production.example .env.production
nano .env.production

# Run
docker-compose -f docker-compose.prod.yml up -d

# Check
curl http://localhost/health
```

## Cloud Platforms

### Railway
1. Connect GitHub repo
2. Add environment variables
3. Set `RAILWAY_DOCKERFILE_PATH=Dockerfile.prod`
4. Deploy

### DigitalOcean App Platform
1. Connect repo
2. Set Dockerfile path: `Dockerfile.prod`
3. Add env vars
4. Deploy

### AWS ECS
```bash
# Build and push
docker build -f Dockerfile.prod -t kick-tts-bot .
docker tag kick-tts-bot:latest <account>.dkr.ecr.region.amazonaws.com/kick-tts-bot:latest
docker push <account>.dkr.ecr.region.amazonaws.com/kick-tts-bot:latest

# Create ECS service (use AWS Console or CLI)
```

## Monitoring

### Health
```bash
watch -n 5 'curl -s http://localhost/health | jq'
```

### Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f --tail=100 tts-bot
```

### Resources
```bash
docker stats kick-tts-bot
```
