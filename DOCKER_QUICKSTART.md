# Docker Quick Start

Empieza en 2 minutos con Docker.

## Paso 1: Instalar Docker

### macOS
```bash
brew install --cask docker
# O descargar de https://www.docker.com/products/docker-desktop
```

### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout y login de nuevo
```

### Windows
Descargar Docker Desktop: https://www.docker.com/products/docker-desktop

---

## Paso 2: Configurar

```bash
cp .env.docker .env
nano .env
```

Editar esta línea:
```bash
KICK_CHANNEL=tu_canal_aqui
```

---

## Paso 3: Iniciar

### Con Redis (recomendado)
```bash
docker-compose up --build -d
```

### Sin Redis (simple)
```bash
docker-compose -f docker-compose.simple.yml up --build -d
```

---

## Paso 4: Verificar

Abrir navegador: http://localhost:8000

---

## Comandos Esenciales

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Detener todo
docker-compose down

# Reiniciar
docker-compose down && docker-compose up --build -d

# Ver estado
docker-compose ps
```

---

## Agregar Sonidos

```bash
# Copiar archivos .mp3 a static/sounds/
cp tu-sonido.mp3 static/sounds/airhorn.mp3

# Usar en chat
!airhorn
```

Los cambios en `static/sounds/` son inmediatos.

---

## OBS Setup

1. Agregar Browser Source
2. URL: `http://localhost:8000/widget?channel=TU_CANAL`
3. Tamaño: 1920x1080
4. Activar "Control audio via OBS"

---

## Troubleshooting

### No arranca
```bash
docker-compose logs -f
```

### Puerto ocupado
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usar 8001 en lugar de 8000
```

### Reiniciar desde cero
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up --build -d
```

---

## Actualizar

```bash
# Si actualizas el código
docker-compose down
docker-compose build
docker-compose up --build -d
```

---

## Desinstalar

```bash
docker-compose down
docker-compose down -v
docker system prune -a
```

---

¡Listo! Ahora tienes el bot corriendo en Docker.
