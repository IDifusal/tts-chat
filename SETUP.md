# Quick Setup Guide

Follow these steps to get Kick TTS Bot running.

## Step 1: System Dependencies

### macOS
```bash
brew install python@3.9 ffmpeg espeak-ng
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip ffmpeg espeak-ng
```

## Step 2: Project Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Download Piper Model

```bash
make download
```

Or manually:
```bash
mkdir -p models
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx -O models/es_ES-davefx-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json -O models/es_ES-davefx-medium.onnx.json
```

## Step 4: Configure

```bash
cp .env.example .env
nano .env
```

Edit these values:
```bash
KICK_CHANNEL=your_channel_name
PIPER_MODEL=models/es_ES-davefx-medium.onnx
```

## Step 5: Run

```bash
make dev
```

Or:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Test

Open browser: http://localhost:8000

You should see the control panel. Test TTS generation from there.

## Step 7: OBS Setup

1. In OBS, add **Browser Source**
2. Set URL: `http://localhost:8000/widget?channel=YOUR_CHANNEL`
3. Set dimensions: 1920x1080
4. Enable "Control audio via OBS"
5. In Audio Mixer, right-click the source
6. Set Audio Monitoring to "Monitor and Output"

## Troubleshooting

### Piper not found
```bash
which piper
pip show piper-tts
```

### FFmpeg not found
```bash
which ffmpeg
ffmpeg -version
```

### Module not found errors
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Can't connect to Kick
- Check that KICK_CHANNEL is spelled correctly
- Check internet connection
- Try a different channel to test

## Next Steps

- Add sound effects to `static/sounds/`
- Customize widget appearance in `templates/widget.html`
- Adjust configuration in `.env`
- Try different Piper voices from https://rhasspy.github.io/piper-samples/
