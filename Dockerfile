FROM python:3.11-slim

WORKDIR /app

# System deps: curl for healthcheck, build tools for piper-tts native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Piper model if not present in the image context
RUN mkdir -p models
COPY models/ models/

# Pull the .onnx model file from HuggingFace if it wasn't copied (large file, often git-ignored)
RUN if [ ! -f models/es_ES-davefx-medium.onnx ]; then \
      curl -L -o models/es_ES-davefx-medium.onnx \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"; \
    fi

# Application code
COPY . .

RUN mkdir -p static/audio static/sounds static/cache data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
