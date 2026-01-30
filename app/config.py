from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Kick TTS Bot"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    KICK_CHANNEL: str
    KICK_WEBSOCKET_URL: str = "wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679"
    
    PIPER_MODEL: str = "models/es_ES-davefx-medium.onnx"
    PIPER_VOICE: str = "es-spanish-male"
    
    AUDIO_OUTPUT_DIR: Path = Path("static/audio")
    SOUNDS_DIR: Path = Path("static/sounds")
    CACHE_DIR: Path = Path("static/cache")
    AUDIO_FORMAT: str = "wav"
    
    ENABLE_REDIS_CACHE: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    MIN_MESSAGE_LENGTH: int = 2
    MAX_MESSAGE_LENGTH: int = 200
    COOLDOWN_SECONDS: int = 1
    IGNORE_COMMANDS: bool = True
    ENABLE_TTS: bool = True
    ENABLE_SOUNDS: bool = True
    
    WIDGET_SHOW_MESSAGES: bool = True
    WIDGET_MESSAGE_DURATION: int = 5000
    WIDGET_MAX_MESSAGES: int = 3
    
    class Config:
        env_file = ".env"


settings = Settings()

settings.AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
