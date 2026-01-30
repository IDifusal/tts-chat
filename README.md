# Kick TTS Bot - Version 1.0

Real-time Text-to-Speech system for Kick.com that listens to chat and generates audio using Piper TTS.

## Features

- Listen to Kick chat via WebSocket
- Generate audio with Piper TTS (fast and local)
- Serve audio via URL for OBS Browser Source
- Sound effects with `!command` triggers
- Cache system for repeated messages
- WebSocket real-time communication
- **Modular event system** (chat, subscriptions, follows)
- **Visual alerts** with animated GIFs and icons

## Architecture

```
Kick WebSocket (Chat + Events)
    ↓
FastAPI Server (port 8000)
    ↓
Event Handlers (Modular)
    ├── Chat → Piper TTS → Audio
    ├── Subscription → Visual Alert
    └── [Future Events]
    ↓
OBS Widget (Browser Source)
```

## Installation

### Prerequisites

**System Dependencies:**

Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip ffmpeg espeak-ng
```

macOS:
```bash
brew install python@3.9 ffmpeg espeak-ng
```

### Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Download Piper model:
```bash
mkdir -p models

# Spanish model (medium quality)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx \
  -O models/es_ES-davefx-medium.onnx

wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json \
  -O models/es_ES-davefx-medium.onnx.json
```

4. Configure environment:
```bash
cp .env.example .env
nano .env  # Edit with your values
```

Required configuration:
```bash
KICK_CHANNEL=your_channel_here
PIPER_MODEL=models/es_ES-davefx-medium.onnx
```

## Running

### Option 1: Docker (Recommended)

```bash
# Configure
cp .env.docker .env
nano .env  # Set KICK_CHANNEL

# Start with Redis
docker-compose up -d

# Or start without Redis (simple)
docker-compose -f docker-compose.simple.yml up -d

# View logs
docker-compose logs -f
```

See full guide: `DOCKER.md`

### Option 2: Development Mode (Local)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Production Mode (Local)

```bash
chmod +x run.sh
./run.sh
```

### Verify Installation

1. Open browser: http://localhost:8000
2. You should see the control panel
3. Widget URL: http://localhost:8000/widget?channel=YOUR_CHANNEL

## OBS Setup

1. Add Browser Source in OBS
2. Configure:
   - URL: `http://localhost:8000/widget?channel=YOUR_CHANNEL`
   - Width: 1920
   - Height: 1080
   - FPS: 30
   - Enable "Control audio via OBS"

3. Configure Audio:
   - Right-click on "Kick TTS Widget" in Audio Mixer
   - Advanced Audio Properties
   - Audio Monitoring: "Monitor and Output"

## Sound Effects

1. Download .mp3 files from:
   - https://freesound.org/
   - https://www.zapsplat.com/
   - https://mixkit.co/

2. Place in `static/sounds/`:
   ```
   static/sounds/
   ├── airhorn.mp3
   ├── applause.mp3
   └── bruh.mp3
   ```

3. Use in chat: `!airhorn`, `!applause`, etc.

## API Endpoints

### Generate TTS
```bash
curl -X POST http://localhost:8000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","username":"test"}'
```

### List Sounds
```bash
curl http://localhost:8000/api/sounds
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Performance

Expected latency:
- Kick WebSocket → Server: 50-200ms
- Process message: 10-50ms
- Piper generate audio: 200-400ms
- Convert WAV→MP3: 50-100ms
- WebSocket → Widget: 50-100ms
- OBS playback: 10-50ms

**Total (first time): 370-900ms**
**Total (cached): 100-200ms**

## Troubleshooting

### Piper not installing
```bash
python --version  # Must be 3.9+
pip uninstall piper-tts
pip install piper-tts
```

### Audio not generating
```bash
# Test Piper
echo "hello world" | piper --model models/es_ES-davefx-medium.onnx --output_file test.wav

# Test ffmpeg
ffmpeg -version
```

### Widget not connecting in OBS
- Verify URL includes correct channel
- Enable "Control audio via OBS"
- Refresh browser source
- Check server logs

### Kick chat not working
- Verify `KICK_CHANNEL` in `.env`
- Check logs for "Subscribed to chatrooms.XXXXX"
- Test with a different channel first

## Project Structure

```
tts-chat/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── services/
│   │   ├── kick_listener.py # Kick WebSocket client
│   │   ├── piper_tts.py     # Piper TTS service
│   │   ├── sound_service.py # Sound effects
│   │   └── cache_service.py # Cache system
│   └── routes/
│       ├── api.py           # API endpoints
│       └── websocket.py     # WebSocket handlers
├── static/
│   ├── audio/               # Generated TTS audio
│   ├── sounds/              # Sound effects (.mp3)
│   └── cache/               # Audio cache
├── templates/
│   ├── index.html           # Control panel
│   └── widget.html          # OBS widget
├── models/                  # Piper models (.onnx)
├── requirements.txt
├── .env.example
└── README.md
```

## Resources

- **Piper TTS**: https://github.com/OHF-Voice/piper1-gpl
- **Available Voices**: https://rhasspy.github.io/piper-samples/
- **Kick API**: https://docs.kick.com/
- **FastAPI**: https://fastapi.tiangolo.com/

## License

MIT
