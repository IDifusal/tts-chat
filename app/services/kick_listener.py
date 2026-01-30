import asyncio
import websockets
import json
from typing import Optional

from app.config import settings
from app.services.piper_tts import get_tts
from app.routes.websocket import broadcast_to_widgets
from app.logger import logger


class KickListener:
    def __init__(self, channel: str):
        self.channel = channel
        self.ws_url = settings.KICK_WEBSOCKET_URL
        self.chatroom_id = None
        self.tts = get_tts()
        self.last_message_time = {}
        
    async def start(self):
        logger.info(f"Connecting to Kick channel: {self.channel}")
        
        await self._get_chatroom_id()
        await self._connect_websocket()
    
    async def _get_chatroom_id(self):
        import aiohttp
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://kick.com/{self.channel}',
            'Origin': 'https://kick.com'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"https://kick.com/api/v2/channels/{self.channel}"
            logger.info(f"Fetching channel info from: {url}")
            
            async with session.get(url) as response:
                status = response.status
                logger.info(f"API Response Status: {status}")
                
                if status == 200:
                    data = await response.json()
                    self.chatroom_id = data['chatroom']['id']
                    logger.info(f"Chatroom ID: {self.chatroom_id}")
                else:
                    text = await response.text()
                    logger.error(f"API Response Body: {text[:500]}")
                    raise RuntimeError(
                        f"Could not get chatroom ID for: {self.channel} (Status: {status})"
                    )
    
    async def _connect_websocket(self):
        ws_url_with_protocol = f"{self.ws_url}?protocol=7&client=js&version=8.4.0-rc2"
        logger.info(f"Connecting to WebSocket: {ws_url_with_protocol}")
        
        async with websockets.connect(ws_url_with_protocol) as websocket:
            # Wait for connection established
            connection_msg = await websocket.recv()
            logger.info(f"WebSocket connection established: {connection_msg[:150]}")
            
            # Subscribe to chatroom (v2 is required for chat messages!)
            subscribe_msg = {
                "event": "pusher:subscribe",
                "data": {
                    "auth": "",
                    "channel": f"chatrooms.{self.chatroom_id}.v2"
                }
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to chatrooms.{self.chatroom_id}.v2")
            
            # Keep connection alive with ping/pong
            ping_task = asyncio.create_task(self._send_ping(websocket))
            
            try:
                async for message in websocket:
                    try:
                        await self._process_message(message)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
            finally:
                ping_task.cancel()
    
    async def _send_ping(self, websocket):
        """Send periodic ping to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(30)
                ping_msg = {"event": "pusher:ping", "data": {}}
                await websocket.send(json.dumps(ping_msg))
        except asyncio.CancelledError:
            pass
    
    async def _process_message(self, message: str):
        data = json.loads(message)
        event_type = data.get("event")
        
        # Skip system events silently
        if event_type in ["pusher:connection_established", "pusher_internal:subscription_succeeded", "pusher:pong"]:
            return
        
        # Check if this is a chat message event
        if "ChatMessageEvent" not in event_type:
            return
        
        try:
            # Parse the event data (it's a JSON string inside the JSON)
            event_data = json.loads(data["data"])
            
            # Extract content and sender directly from event_data
            content = event_data.get("content", "")
            sender = event_data.get("sender", {})
            username = sender.get("username", "unknown")
            
            # Ignore KickBot messages
            if username.lower() == "kickbot":
                return
            
            # Simple log: only username and message
            logger.info(f"{username}: {content}")
            
            if not self._check_cooldown(username):
                return
            
            if content.startswith("!") and settings.ENABLE_SOUNDS:
                await self._handle_sound_command(content, username)
                return
            
            if settings.ENABLE_TTS:
                await self._handle_tts_message(content, username)
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
    
    def _check_cooldown(self, username: str) -> bool:
        import time
        
        now = time.time()
        last_time = self.last_message_time.get(username, 0)
        
        if now - last_time < settings.COOLDOWN_SECONDS:
            return False
        
        self.last_message_time[username] = now
        return True
    
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
