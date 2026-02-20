import asyncio
from typing import Dict

from app.services.kick_listener import KickListener
from app.logger import logger


class StreamManager:
    """Manages one KickListener task per stream_id."""

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start_all(self, streams: list[dict]):
        for stream in streams:
            await self.start_stream(
                stream["stream_id"],
                stream["channel"],
                tts_backend=stream.get("tts_backend", "elevenlabs"),
                elevenlabs_voice_id=stream.get("elevenlabs_voice_id"),
            )

    async def start_stream(
        self,
        stream_id: str,
        channel: str,
        tts_backend: str = "elevenlabs",
        elevenlabs_voice_id: str | None = None,
    ):
        existing = self._tasks.get(stream_id)
        if existing and not existing.done():
            logger.info(f"Listener for stream '{stream_id}' is already running.")
            return

        listener = KickListener(
            channel=channel,
            stream_id=stream_id,
            tts_backend=tts_backend,
            elevenlabs_voice_id=elevenlabs_voice_id,
        )
        task = asyncio.create_task(listener.start(), name=f"kick-{stream_id}")
        self._tasks[stream_id] = task
        logger.info(
            f"Started listener for stream '{stream_id}' → channel '{channel}' "
            f"(tts={tts_backend})"
        )

    async def stop_stream(self, stream_id: str):
        task = self._tasks.pop(stream_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped listener for stream '{stream_id}'")

    def get_running_streams(self) -> list[str]:
        return [sid for sid, task in self._tasks.items() if not task.done()]


stream_manager = StreamManager()
