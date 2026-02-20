import asyncio
import websockets
import json
from typing import Optional

from app.config import settings
from app.logger import logger
from app.events import make_handlers, handle_event
from app.services.tts import build_tts


class KickListener:
    def __init__(
        self,
        channel: str,
        stream_id: str,
        tts_backend: str = "piper",
        elevenlabs_voice_id: str | None = None,
    ):
        self.channel = channel
        self.stream_id = stream_id
        self.ws_url = settings.KICK_WEBSOCKET_URL
        self.chatroom_id = None

        tts = build_tts(tts_backend, elevenlabs_voice_id)
        self._handlers = make_handlers(tts)

    async def start(self):
        logger.info(
            f"Connecting to Kick channel: {self.channel} "
            f"(stream_id={self.stream_id})"
        )
        await self._get_chatroom_id()
        await self._connect_websocket()

    async def _get_chatroom_id(self):
        import aiohttp

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://kick.com/{self.channel}',
            'Origin': 'https://kick.com',
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
            connection_msg = await websocket.recv()
            logger.info(f"WebSocket connection established: {connection_msg[:150]}")

            subscribe_msg = {
                "event": "pusher:subscribe",
                "data": {
                    "auth": "",
                    "channel": f"chatrooms.{self.chatroom_id}.v2",
                },
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to chatrooms.{self.chatroom_id}.v2")

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
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send(json.dumps({"event": "pusher:ping", "data": {}}))
        except asyncio.CancelledError:
            pass

    async def _process_message(self, message: str):
        data = json.loads(message)
        event_type = data.get("event")

        if event_type in [
            "pusher:connection_established",
            "pusher_internal:subscription_succeeded",
            "pusher:pong",
        ]:
            return

        if not event_type.startswith("App\\Events\\"):
            return

        try:
            event_data = json.loads(data["data"])
            await handle_event(event_type, event_data, self.stream_id, self._handlers)
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}")
