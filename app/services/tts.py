"""
Punto de entrada unificado para TTS.
Backend configurable: openai (más barato) o elevenlabs.
"""
from app.config import settings
from app.services.elevenlabs_tts import ElevenLabsTTS, get_elevenlabs_tts
from app.services.openai_tts import OpenAITTS, get_openai_tts


_tts_instance = None


def get_tts() -> OpenAITTS | ElevenLabsTTS:
    """Devuelve el backend TTS según TTS_BACKEND (openai o elevenlabs)."""
    global _tts_instance
    if _tts_instance is None:
        backend = (settings.TTS_BACKEND or "openai").strip().lower()
        if backend == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY no está configurada. Añádela en .env para usar TTS con OpenAI."
                )
            _tts_instance = get_openai_tts()
        elif backend == "elevenlabs":
            if not settings.ELEVEN_LABS_API_KEY:
                raise ValueError(
                    "ELEVEN_LABS_API_KEY no está configurada. Añádela en .env para usar TTS con ElevenLabs."
                )
            _tts_instance = get_elevenlabs_tts()
        else:
            raise ValueError(
                f"TTS_BACKEND inválido: {settings.TTS_BACKEND}. Usa 'openai' o 'elevenlabs'."
            )
    return _tts_instance
