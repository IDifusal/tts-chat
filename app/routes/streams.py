from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_all_streams, get_stream, add_stream, update_stream_channel, delete_stream
from app.services.stream_manager import stream_manager

router = APIRouter()


class StreamCreateRequest(BaseModel):
    stream_id: str
    channel: str


class StreamUpdateRequest(BaseModel):
    channel: str


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
    """Add a new stream_id → channel mapping and start its listener."""
    if await get_stream(req.stream_id):
        raise HTTPException(status_code=409, detail="stream_id already exists")

    await add_stream(req.stream_id, req.channel)
    await stream_manager.start_stream(req.stream_id, req.channel)

    return {"stream_id": req.stream_id, "channel": req.channel}


@router.put("/streams/{stream_id}")
async def update_stream(stream_id: str, req: StreamUpdateRequest):
    """Change the channel for an existing stream and restart its listener."""
    if not await get_stream(stream_id):
        raise HTTPException(status_code=404, detail="stream not found")

    await update_stream_channel(stream_id, req.channel)

    # Restart listener with new channel
    await stream_manager.stop_stream(stream_id)
    await stream_manager.start_stream(stream_id, req.channel)

    return {"stream_id": stream_id, "channel": req.channel}


@router.delete("/streams/{stream_id}")
async def remove_stream(stream_id: str):
    """Remove a stream mapping and stop its listener."""
    if not await delete_stream(stream_id):
        raise HTTPException(status_code=404, detail="stream not found")

    await stream_manager.stop_stream(stream_id)

    return {"status": "deleted", "stream_id": stream_id}
