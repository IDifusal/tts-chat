import hashlib
import os
import wave
from pathlib import Path
from datetime import datetime
import time
import subprocess

from piper import PiperVoice

from app.config import settings


class PiperTTS:
    def __init__(self):
        self.model_path = settings.PIPER_MODEL
        self.cache_dir = settings.CACHE_DIR
        self.output_dir = settings.AUDIO_OUTPUT_DIR
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Piper model not found: {self.model_path}"
            )
        
        print(f"Loading Piper voice model: {self.model_path}")
        self.voice = PiperVoice.load(str(self.model_path))
        print("Piper TTS initialized successfully")
    
    def generate(
        self, 
        text: str, 
        username: str = None,
        use_cache: bool = True
    ) -> tuple[str, bool, float]:
        """
        Generate TTS audio with Piper
        
        Returns:
            tuple: (audio_url, was_cached, generation_time_ms)
        """
        
        start_time = time.time()
        cached = False
        
        if use_cache:
            cache_key = self._get_cache_key(text, username)
            cached_path = self.cache_dir / f"{cache_key}.wav"
            
            if cached_path.exists():
                print(f"Cache hit: {cache_key}")
                elapsed = (time.time() - start_time) * 1000
                return f"/static/cache/{cache_key}.wav", True, elapsed
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{username or 'user'}_{timestamp}"
        
        wav_path = self.output_dir / f"{filename}.wav"
        
        try:
            with wave.open(str(wav_path), "wb") as wav_file:
                self.voice.synthesize_wav(text, wav_file)
            
        except Exception as e:
            raise RuntimeError(f"Piper synthesis error: {e}")
        
        if use_cache:
            cache_path = self.cache_dir / f"{cache_key}.wav"
            subprocess.run(['cp', str(wav_path), str(cache_path)], check=False)
        
        elapsed = (time.time() - start_time) * 1000
        print(f"TTS generated in {elapsed:.0f}ms: {filename}.wav")
        
        return f"/static/audio/{filename}.wav", cached, elapsed
    
    def _get_cache_key(self, text: str, username: str = None) -> str:
        content = f"{text}_{username or 'default'}"
        return hashlib.md5(content.encode()).hexdigest()


_tts_instance = None

def get_tts() -> PiperTTS:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = PiperTTS()
    return _tts_instance
