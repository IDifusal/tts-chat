from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # Ignorar variables del .env que ya no existen (ej. PIPER_*)
    )
    APP_NAME: str = "Kick TTS Bot"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    KICK_CHANNEL: str
    KICK_WEBSOCKET_URL: str = "wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679"

    ELEVEN_LABS_API_KEY: str = ""
    ELEVEN_LABS_VOICE_ID: str = "86V9x9hrQds83qf7zaGn"
    ELEVEN_LABS_MODEL_ID: str = "eleven_multilingual_v2"
    # Voice settings (tono más sensual: estabilidad baja, velocidad un poco más lenta)
    # stability 0-1: bajo = más expresivo/emocional; similarity_boost: cercanía a la voz; speed 0.7-1.2: <1 = más lento
    ELEVEN_LABS_STABILITY: float = 0.4
    ELEVEN_LABS_SIMILARITY_BOOST: float = 0.8
    ELEVEN_LABS_STYLE: float = 0.2
    ELEVEN_LABS_SPEED: float = 0.92
    
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


settings = Settings()

settings.AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
