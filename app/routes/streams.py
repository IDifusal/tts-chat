from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.database import get_all_streams, get_stream, add_stream, update_stream, delete_stream
from app.services.stream_manager import stream_manager

router = APIRouter()


class StreamCreateRequest(BaseModel):
    stream_id: str
    channel: str
    tts_backend: str = "elevenlabs"
    elevenlabs_voice_id: Optional[str] = None  # uses global ELEVEN_LABS_VOICE_ID if omitted


class StreamUpdateRequest(BaseModel):
    channel: Optional[str] = None
    tts_backend: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None


@router.get("/streams")
async def list_streams():
    """List all configured streams with their running status."""
    streams = await get_all_streams()
    running = stream_manager.get_running_streams()
    for s in streams:
        s["running"] = s["stream_id"] in running
    return {"streams": streams}


@router.post("/streams", status_code=201)
async def create_stream(req: StreamCreateRequest):
    """Add a new stream and start its listener."""
    if req.tts_backend not in ("piper", "elevenlabs"):
        raise HTTPException(status_code=400, detail="tts_backend must be 'piper' or 'elevenlabs'")

    if await get_stream(req.stream_id):
        raise HTTPException(status_code=409, detail="stream_id already exists")

    await add_stream(
        req.stream_id,
        req.channel,
        tts_backend=req.tts_backend,
        elevenlabs_voice_id=req.elevenlabs_voice_id,
    )
    await stream_manager.start_stream(
        req.stream_id,
        req.channel,
        tts_backend=req.tts_backend,
        elevenlabs_voice_id=req.elevenlabs_voice_id,
    )

    return {
        "stream_id": req.stream_id,
        "channel": req.channel,
        "tts_backend": req.tts_backend,
        "elevenlabs_voice_id": req.elevenlabs_voice_id,
    }


@router.put("/streams/{stream_id}")
async def update_stream_route(stream_id: str, req: StreamUpdateRequest):
    """Update channel and/or voice config for a stream, then restart its listener."""
    stream = await get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="stream not found")

    if req.tts_backend and req.tts_backend not in ("piper", "elevenlabs"):
        raise HTTPException(status_code=400, detail="tts_backend must be 'piper' or 'elevenlabs'")

    await update_stream(
        stream_id,
        channel=req.channel,
        tts_backend=req.tts_backend,
        elevenlabs_voice_id=req.elevenlabs_voice_id,
    )

    updated = await get_stream(stream_id)

    await stream_manager.stop_stream(stream_id)
    await stream_manager.start_stream(
        stream_id,
        updated["channel"],
        tts_backend=updated["tts_backend"],
        elevenlabs_voice_id=updated["elevenlabs_voice_id"],
    )

    return updated


@router.delete("/streams/{stream_id}")
async def remove_stream(stream_id: str):
    """Remove a stream and stop its listener."""
    if not await delete_stream(stream_id):
        raise HTTPException(status_code=404, detail="stream not found")

    await stream_manager.stop_stream(stream_id)

    return {"status": "deleted", "stream_id": stream_id}
