import time
from typing import Dict, Any

from app.config import settings
from app.services.piper_tts import get_tts
from app.routes.websocket import broadcast_to_widgets
from app.logger import logger
from app.events.base import EventHandler


class ChatEventHandler(EventHandler):
    def __init__(self):
        self.tts = get_tts()
        self.last_message_time = {}
    
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        sender = event_data.get("sender", {})
        username = sender.get("username", "").lower()
        
        # Ignore KickBot
        if username == "kickbot":
            return False
        
        return True
    
    def _check_cooldown(self, username: str) -> bool:
        now = time.time()
        last_time = self.last_message_time.get(username, 0)
        
        if now - last_time < settings.COOLDOWN_SECONDS:
            return False
        
        self.last_message_time[username] = now
        return True
    
    async def handle(self, event_data: Dict[str, Any]):
        if not self.should_process(event_data):
            return
        
        content = event_data.get("content", "")
        sender = event_data.get("sender", {})
        username = sender.get("username", "unknown")
        
        logger.info(f"{username}: {content}")
        
        if not self._check_cooldown(username):
            return
        
        # Sound commands
        if content.startswith("!") and settings.ENABLE_SOUNDS:
            await self._handle_sound_command(content, username)
            return
        
        # TTS messages
        if settings.ENABLE_TTS:
            await self._handle_tts_message(content, username)
    
    async def _handle_sound_command(self, content: str, username: str):
        sound_name = content[1:].split()[0]
        sound_path = settings.SOUNDS_DIR / f"{sound_name}.mp3"
        
        if sound_path.exists():
            logger.info(f"Playing sound: {sound_name} (requested by {username})")
            
            await broadcast_to_widgets({
                'type': 'sound_effect',
                'sound_name': sound_name,
                'audio_url': f"/static/sounds/{sound_name}.mp3",
                'username': username
            })
        else:
            logger.warning(f"Sound not found: {sound_name}")
    
    async def _handle_tts_message(self, content: str, username: str):
        if len(content) < settings.MIN_MESSAGE_LENGTH:
            logger.debug(f"Message too short ({len(content)} chars), skipping")
            return
        
        if len(content) > settings.MAX_MESSAGE_LENGTH:
            content = content[:settings.MAX_MESSAGE_LENGTH]
        
        try:
            logger.info(f"Generating TTS for {username}: {content[:50]}...")
            audio_url, cached, gen_time = self.tts.generate(content, username)
            
            await broadcast_to_widgets({
                'type': 'tts_message',
                'username': username,
                'text': content,
                'audio_url': audio_url,
                'cached': cached,
                'generation_time_ms': gen_time
            })
            
            logger.info(f"TTS generated: {audio_url} ({gen_time:.0f}ms, cached={cached})")
            
        except Exception as e:
            logger.error(f"TTS generation error: {e}", exc_info=True)
