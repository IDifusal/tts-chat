import hashlib
import shutil
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from app.config import settings


class OpenAITTS:
    """TTS usando la API de OpenAI (más barato: ~$0.015 por 1000 caracteres)."""

    OUTPUT_EXT = "mp3"

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_TTS_MODEL
        self.voice = settings.OPENAI_TTS_VOICE
        self.speed = settings.OPENAI_TTS_SPEED
        self.cache_dir = settings.CACHE_DIR
        self.output_dir = settings.AUDIO_OUTPUT_DIR

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no está configurada")

        self._client = OpenAI(api_key=self.api_key)
        print(f"OpenAI TTS inicializado (model={self.model}, voice={self.voice})")

    def generate(
        self,
        text: str,
        username: str = None,
        use_cache: bool = True,
    ) -> tuple[str, bool, float]:
        """
        Genera audio TTS con OpenAI.

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
            response = self._client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="mp3",
                speed=self.speed,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS API error: {e}") from e

        if hasattr(response, "stream_to_file"):
            response.stream_to_file(out_path)
        else:
            out_path.write_bytes(response.content if hasattr(response, "content") else b"".join(response))

        if use_cache:
            cache_path = self.cache_dir / f"{cache_key}.{self.OUTPUT_EXT}"
            shutil.copy(out_path, cache_path)

        elapsed = (time.time() - start_time) * 1000
        print(f"TTS generado en {elapsed:.0f}ms: {filename}.{self.OUTPUT_EXT}")

        return f"/static/audio/{filename}.{self.OUTPUT_EXT}", cached, elapsed

    def _get_cache_key(self, text: str, username: str = None) -> str:
        content = f"{text}_{username or 'default'}_{self.model}_{self.voice}_{self.speed}"
        return hashlib.md5(content.encode()).hexdigest()


_openai_tts_instance = None


def get_openai_tts() -> OpenAITTS:
    global _openai_tts_instance
    if _openai_tts_instance is None:
        _openai_tts_instance = OpenAITTS()
    return _openai_tts_instance
