import hashlib
import time
from datetime import datetime
from pathlib import Path

from elevenlabs.client import ElevenLabs

from app.config import settings


class ElevenLabsTTS:
    """TTS usando el SDK oficial de ElevenLabs."""

    OUTPUT_EXT = "mp3"
    OUTPUT_FORMAT = "mp3_44100_128"

    def __init__(self):
        self.api_key = settings.ELEVEN_LABS_API_KEY
        self.voice_id = settings.ELEVEN_LABS_VOICE_ID
        self.model_id = settings.ELEVEN_LABS_MODEL_ID
        self.cache_dir = settings.CACHE_DIR
        self.output_dir = settings.AUDIO_OUTPUT_DIR
        self._voice_settings = {
            "stability": settings.ELEVEN_LABS_STABILITY,
            "similarity_boost": settings.ELEVEN_LABS_SIMILARITY_BOOST,
            "style": settings.ELEVEN_LABS_STYLE,
            "speed": settings.ELEVEN_LABS_SPEED,
        }

        if not self.api_key:
            raise ValueError("ELEVEN_LABS_API_KEY no está configurada")

        self._client = ElevenLabs(api_key=self.api_key)
        print(f"ElevenLabs TTS inicializado (voice_id={self.voice_id})")

    def generate(
        self,
        text: str,
        username: str = None,
        use_cache: bool = True,
    ) -> tuple[str, bool, float]:
        """
        Genera audio TTS con ElevenLabs.

        Returns:
            tuple: (audio_url, was_cached, generation_time_ms)
        """
        start_time = time.time()
        cached = False

        if use_cache:
            cache_key = self._get_cache_key(text, username)
            cached_path = self.cache_dir / f"{cache_key}.{self.OUTPUT_EXT}"

            if cached_path.exists():
                print(f"Cache hit: {cache_key}")
                elapsed = (time.time() - start_time) * 1000
                return f"/static/cache/{cache_key}.{self.OUTPUT_EXT}", True, elapsed

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{username or 'user'}_{timestamp}"
        out_path = self.output_dir / f"{filename}.{self.OUTPUT_EXT}"

        try:
            audio = self._client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model_id,
                output_format=self.OUTPUT_FORMAT,
                voice_settings=self._voice_settings,
            )
        except Exception as e:
            detail = str(e)
            if hasattr(e, "body") and e.body:
                detail = getattr(e.body, "message", e.body) or detail
            raise RuntimeError(f"ElevenLabs API error: {detail}") from e

        # SDK devuelve bytes (audio en formato mp3)
        content = audio if isinstance(audio, bytes) else b"".join(audio)
        out_path.write_bytes(content)

        if use_cache:
            cache_path = self.cache_dir / f"{cache_key}.{self.OUTPUT_EXT}"
            cache_path.write_bytes(content)

        elapsed = (time.time() - start_time) * 1000
        print(f"TTS generado en {elapsed:.0f}ms: {filename}.{self.OUTPUT_EXT}")

        return f"/static/audio/{filename}.{self.OUTPUT_EXT}", cached, elapsed

    def _get_cache_key(self, text: str, username: str = None) -> str:
        # Incluir voice_settings en cache para que cambios de tono generen nuevo audio
        settings_suffix = "_".join(f"{k}={v}" for k, v in sorted(self._voice_settings.items()))
        content = f"{text}_{username or 'default'}_{settings_suffix}"
        return hashlib.md5(content.encode()).hexdigest()


_elevenlabs_instance = None


def get_elevenlabs_tts() -> ElevenLabsTTS:
    global _elevenlabs_instance
    if _elevenlabs_instance is None:
        _elevenlabs_instance = ElevenLabsTTS()
    return _elevenlabs_instance
