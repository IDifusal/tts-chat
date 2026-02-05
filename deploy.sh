cat << 'EOF' > ~/deploy.sh
#!/usr/bin/env bash
set -euo pipefail

echo "==> Deteniendo n8n para liberar RAM..."
docker stop n8n 2>/dev/null || true

echo "==> Actualizando repositorio tts-chat..."
cd ~/tts-chat
git pull origin main || true

echo "==> Deteniendo contenedores antiguos..."
docker compose -f docker-compose.simple.yml down 2>/dev/null || true

echo "==> Construyendo imagen actualizada..."
docker compose -f docker-compose.simple.yml build --no-cache

echo "==> Levantando tts-chat..."
docker compose -f docker-compose.simple.yml up -d

echo "==> Esperando a que el contenedor esté healthy..."
sleep 5

echo "==> Levantando n8n nuevamente..."
docker start n8n 2>/dev/null || \
docker run -d --name n8n \
  -p 127.0.0.1:5678:5678 \
  --restart unless-stopped \
  n8nio/n8n:1.116.2

echo "==> Verificación de contenedores:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "==> Logs de tts-chat (últimas 30 líneas):"
docker compose -f docker-compose.simple.yml logs --tail=30

echo "==> ✅ Deploy completado!"
echo "==> Accede a: https://test.espanglishmarketing.com/widget"
EOF
