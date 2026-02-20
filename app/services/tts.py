"""
TTS factory.
Default backend: ElevenLabs (optional voice_id per stream).
Fallback: Piper (local, runs when ElevenLabs fails or has no credits).
"""
from app.logger import logger


class FallbackTTS:
    """
    Tries the primary TTS backend first.
    On any exception falls back to Piper silently so the stream keeps working.
    """

    def __init__(self, primary, fallback):
        self._primary = primary
        self._fallback = fallback

    def generate(
        self,
        text: str,
        username: str = None,
        use_cache: bool = True,
    ) -> tuple[str, bool, float]:
        try:
            return self._primary.generate(text, username, use_cache)
        except Exception as e:
            logger.warning(f"Primary TTS failed ({e}), falling back to Piper")
            return self._fallback.generate(text, username, use_cache)


def build_tts(backend: str = "elevenlabs", elevenlabs_voice_id: str | None = None):
    """
    Build a TTS instance for a stream.

    Args:
        backend: 'elevenlabs' (default) or 'piper'
        elevenlabs_voice_id: optional per-stream voice override; falls back to
                             global ELEVEN_LABS_VOICE_ID from config if not set.
    """
    backend = (backend or "elevenlabs").strip().lower()

    from app.services.piper_tts import get_piper_tts
    piper = get_piper_tts()

    if backend == "piper":
        return piper

    if backend == "elevenlabs":
        from app.config import settings
        if not settings.ELEVEN_LABS_API_KEY:
            logger.warning("ELEVEN_LABS_API_KEY not set — using Piper only")
            return piper

        from app.services.elevenlabs_tts import ElevenLabsTTS
        elevenlabs = ElevenLabsTTS(voice_id=elevenlabs_voice_id)
        return FallbackTTS(primary=elevenlabs, fallback=piper)

    raise ValueError(f"Unknown TTS backend: '{backend}'. Use 'elevenlabs' or 'piper'.")
