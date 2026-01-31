"""
Punto de entrada unificado para TTS.
Usa ElevenLabs cuando ELEVEN_LABS_API_KEY está configurada, sino Piper (comportamiento actual).
"""
from typing import Union

from app.config import settings

from app.services.piper_tts import PiperTTS, get_tts as get_piper_tts
from app.services.elevenlabs_tts import ElevenLabsTTS, get_elevenlabs_tts


_tts_instance = None


def get_tts() -> Union[PiperTTS, ElevenLabsTTS]:
    """Devuelve el backend TTS según configuración: ElevenLabs si hay API key, sino Piper."""
    global _tts_instance
    if _tts_instance is None:
        if settings.ELEVEN_LABS_API_KEY:
            _tts_instance = get_elevenlabs_tts()
        else:
            _tts_instance = get_piper_tts()
    return _tts_instance
