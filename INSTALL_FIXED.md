# Instalación Corregida - Kick TTS Bot

## ¡Actualización Importante!

Ahora usamos la biblioteca Python `piper-tts` directamente, que es mucho más simple.

## Instalación Rápida

### Paso 1: Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará automáticamente `piper-tts` desde PyPI.

### Paso 3: Descargar modelo de voz

```bash
# Usar el script
make download

# O manualmente
mkdir -p models
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx -O models/es_ES-davefx-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json -O models/es_ES-davefx-medium.onnx.json
```

### Paso 4: Configurar

```bash
cp .env.example .env
nano .env  # Configurar KICK_CHANNEL
```

### Paso 5: Ejecutar

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente:
```bash
make dev
```

## Verificar Instalación

```bash
python3 << EOF
from piper import PiperVoice
print("✓ piper-tts instalado correctamente")
EOF
```

## Ventajas del Nuevo Método

✓ **Más simple** - Solo `pip install`
✓ **Sin binarios** - Todo en Python
✓ **Más rápido** - API nativa de Python
✓ **Mejor integración** - Sin subprocess
✓ **Menos dependencias** - No necesita FFmpeg para generar audio

## Docker

El Dockerfile también está actualizado y funcionará automáticamente:

```bash
make docker-up
```

## Troubleshooting

### Error al importar piper

```bash
pip install --upgrade piper-tts
```

### Modelo no encontrado

```bash
make download
```

### ModuleNotFoundError

```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate
pip install -r requirements.txt
```

## Notas

- Ya NO necesitas instalar el binario `piper`
- Ya NO necesitas FFmpeg para generar el audio WAV
- El audio se genera directamente en formato WAV
- Mucho más simple y confiable
