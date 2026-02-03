"""
Punto de entrada unificado para TTS.
Usa ElevenLabs (requiere ELEVEN_LABS_API_KEY en .env).
"""
from app.config import settings
from app.services.elevenlabs_tts import ElevenLabsTTS, get_elevenlabs_tts


_tts_instance = None


def get_tts() -> ElevenLabsTTS:
    """Devuelve el backend TTS (ElevenLabs). Requiere ELEVEN_LABS_API_KEY configurada."""
    global _tts_instance
    if _tts_instance is None:
        if not settings.ELEVEN_LABS_API_KEY:
            raise ValueError(
                "ELEVEN_LABS_API_KEY no está configurada. Añádela en .env para usar TTS."
            )
        _tts_instance = get_elevenlabs_tts()
    return _tts_instance
