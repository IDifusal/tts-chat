import hashlib
import io
import time
import wave
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.logger import logger


class PiperTTS:
    """Local TTS using Piper — no API key, no cost, runs entirely on-device."""

    OUTPUT_EXT = "wav"

    def __init__(self):
        from piper.voice import PiperVoice

        model_path = Path(settings.PIPER_MODEL)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Piper model not found: {model_path}. "
                "Download it and set PIPER_MODEL in .env"
            )

        self._voice = PiperVoice.load(str(model_path))
        self.cache_dir = settings.CACHE_DIR
        self.output_dir = settings.AUDIO_OUTPUT_DIR
        logger.info(f"Piper TTS loaded: {model_path.name}")

    def generate(
        self,
        text: str,
        username: str = None,
        use_cache: bool = True,
    ) -> tuple[str, bool, float]:
        """
        Synthesize text with Piper.

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

        audio_bytes = self._synthesize(text)
        out_path.write_bytes(audio_bytes)

        if use_cache:
            cache_key = self._get_cache_key(text)
            (self.cache_dir / f"{cache_key}.{self.OUTPUT_EXT}").write_bytes(audio_bytes)

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Piper TTS generated in {elapsed:.0f}ms: {filename}")

        return f"/static/audio/{filename}", False, elapsed

    def _synthesize(self, text: str) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            self._voice.synthesize(text, wav_file)
        return buf.getvalue()

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(f"piper:{text}".encode()).hexdigest()


_piper_instance: PiperTTS | None = None


def get_piper_tts() -> PiperTTS:
    global _piper_instance
    if _piper_instance is None:
        _piper_instance = PiperTTS()
    return _piper_instance
