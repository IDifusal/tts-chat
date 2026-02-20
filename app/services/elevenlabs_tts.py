import hashlib
import time
from datetime import datetime
from pathlib import Path

from elevenlabs.client import ElevenLabs

from app.config import settings
from app.logger import logger


class ElevenLabsTTS:
    """TTS using the official ElevenLabs SDK. voice_id can be overridden per-stream."""

    OUTPUT_EXT = "mp3"
    OUTPUT_FORMAT = "mp3_44100_128"

    def __init__(self, voice_id: str | None = None):
        self.api_key = settings.ELEVEN_LABS_API_KEY
        if not self.api_key:
            raise ValueError("ELEVEN_LABS_API_KEY is not set")

        # Per-stream voice_id takes priority; falls back to global config
        self.voice_id = voice_id or settings.ELEVEN_LABS_VOICE_ID
        self.model_id = settings.ELEVEN_LABS_MODEL_ID
        self.cache_dir = settings.CACHE_DIR
        self.output_dir = settings.AUDIO_OUTPUT_DIR
        self._voice_settings = {
            "stability": settings.ELEVEN_LABS_STABILITY,
            "similarity_boost": settings.ELEVEN_LABS_SIMILARITY_BOOST,
            "style": settings.ELEVEN_LABS_STYLE,
            "speed": settings.ELEVEN_LABS_SPEED,
        }

        self._client = ElevenLabs(api_key=self.api_key)
        logger.info(f"ElevenLabs TTS initialized (voice_id={self.voice_id})")

    def generate(
        self,
        text: str,
        username: str = None,
        use_cache: bool = True,
    ) -> tuple[str, bool, float]:
        """
        Synthesize text with ElevenLabs.

        Returns:
            (audio_url, was_cached, generation_time_ms)
        """
        start_time = time.time()

        if use_cache:
            cache_key = self._get_cache_key(text)
            cached_path = self.cache_dir / f"{cache_key}.{self.OUTPUT_EXT}"
            if cached_path.exists():
                elapsed = (time.time() - start_time) * 1000
                return f"/static/cache/{cache_key}.{self.OUTPUT_EXT}", True, elapsed

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{username or 'user'}_{timestamp}.{self.OUTPUT_EXT}"
        out_path = self.output_dir / filename

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

        content = audio if isinstance(audio, bytes) else b"".join(audio)
        out_path.write_bytes(content)

        if use_cache:
            cache_key = self._get_cache_key(text)
            (self.cache_dir / f"{cache_key}.{self.OUTPUT_EXT}").write_bytes(content)

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"ElevenLabs TTS generated in {elapsed:.0f}ms: {filename}")

        return f"/static/audio/{filename}", False, elapsed

    def _get_cache_key(self, text: str) -> str:
        settings_suffix = "_".join(f"{k}={v}" for k, v in sorted(self._voice_settings.items()))
        content = f"elevenlabs:{self.voice_id}:{settings_suffix}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
