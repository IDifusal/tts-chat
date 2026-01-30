from pydantic import BaseModel
from typing import Optional


class TTSRequest(BaseModel):
    text: str
    username: Optional[str] = None
    use_cache: bool = True


class TTSResponse(BaseModel):
    audio_url: str
    cached: bool = False
    generation_time_ms: Optional[float] = None


class ChatMessage(BaseModel):
    username: str
    text: str
    message_type: str = "chat"


class SoundEffectRequest(BaseModel):
    sound_name: str
    username: Optional[str] = None


class WebSocketMessage(BaseModel):
    type: str
    username: Optional[str] = None
    text: Optional[str] = None
    audio_url: Optional[str] = None
    sound_name: Optional[str] = None
