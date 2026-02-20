import asyncio
import websockets
import json
from typing import Optional

from app.config import settings
from app.logger import logger
from app.events import handle_event


class KickListener:
    def __init__(self, channel: str, stream_id: str):
        self.channel = channel
        self.stream_id = stream_id
        self.ws_url = settings.KICK_WEBSOCKET_URL
        self.chatroom_id = None

    async def start(self):
        logger.info(f"Connecting to Kick channel: {self.channel} (stream_id={self.stream_id})")
        
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
        
        # Check if this is a Kick event
        if not event_type.startswith("App\\Events\\"):
            return
        
        try:
            # Parse the event data (it's a JSON string inside the JSON)
            event_data = json.loads(data["data"])
            
            # Route to appropriate event handler
            await handle_event(event_type, event_data, self.stream_id)
            
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}")
