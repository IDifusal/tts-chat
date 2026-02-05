#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.simple.yml"
N8N_IMAGE="n8nio/n8n:1.116.2"
N8N_PORT="127.0.0.1:5678:5678"
TTS_URL="https://test.espanglishmarketing.com/widget"

echo "==> (1/9) Deteniendo n8n para liberar RAM..."
docker stop n8n 2>/dev/null || true

echo "==> (2/9) Actualizando repositorio tts-chat..."
cd ~/tts-chat
git fetch origin || true
git reset --hard origin/main || true

echo "==> (3/9) Bajando contenedores antiguos de tts-chat..."
docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true

echo "==> (4/9) Limpieza ligera (imágenes dangling y build cache)..."
docker image prune -f >/dev/null 2>&1 || true
docker builder prune -f >/dev/null 2>&1 || true

echo "==> (5/9) Construyendo imagen actualizada (sin cache)..."
docker compose -f "$COMPOSE_FILE" build --no-cache

echo "==> (6/9) Levantando tts-chat..."
docker compose -f "$COMPOSE_FILE" up -d

echo "==> (7/9) Esperando 8s..."
sleep 8

echo "==> (8/9) Levantando n8n nuevamente (sin conflictos)..."
if docker ps -a --format '{{.Names}}' | grep -qx 'n8n'; then
  docker start n8n >/dev/null
else
  docker run -d --name n8n \
    -p "$N8N_PORT" \
    --restart unless-stopped \
    "$N8N_IMAGE" >/dev/null
fi

echo "==> (9/9) Verificación de contenedores:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "==> Logs de tts-chat (últimas 60 líneas):"
docker compose -f "$COMPOSE_FILE" logs --tail=60

echo "==> ✅ Deploy completado!"
echo "==> Accede a: $TTS_URL"
