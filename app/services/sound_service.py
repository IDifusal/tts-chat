from pathlib import Path
from typing import List, Optional

from app.config import settings


class SoundService:
    def __init__(self):
        self.sounds_dir = settings.SOUNDS_DIR
        
    def get_available_sounds(self) -> List[str]:
        """Get list of available sound effects"""
        sounds = []
        for file in self.sounds_dir.glob("*.mp3"):
            sounds.append(file.stem)
        return sorted(sounds)
    
    def sound_exists(self, sound_name: str) -> bool:
        """Check if a sound effect exists"""
        sound_path = self.sounds_dir / f"{sound_name}.mp3"
        return sound_path.exists()
    
    def get_sound_url(self, sound_name: str) -> Optional[str]:
        """Get URL for a sound effect"""
        if self.sound_exists(sound_name):
            return f"/static/sounds/{sound_name}.mp3"
        return None


_sound_service_instance = None

def get_sound_service() -> SoundService:
    global _sound_service_instance
    if _sound_service_instance is None:
        _sound_service_instance = SoundService()
    return _sound_service_instance
