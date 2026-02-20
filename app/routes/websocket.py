from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter()

# Per-stream connections: { stream_id: [WebSocket, ...] }
_connections: Dict[str, List[WebSocket]] = {}


async def broadcast_to_stream(stream_id: str, message: dict):
    """Send a message to all widgets connected to a specific stream."""
    connections = _connections.get(stream_id, [])
    disconnected = []

    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        connections.remove(ws)


async def broadcast_to_widgets(message: dict):
    """Broadcast to ALL streams (kept for backward-compat with existing API routes)."""
    for stream_id in list(_connections.keys()):
        await broadcast_to_stream(stream_id, message)


@router.websocket("/{stream_id}/events")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint scoped to a single stream."""
    await websocket.accept()

    if stream_id not in _connections:
        _connections[stream_id] = []
    _connections[stream_id].append(websocket)

    total = sum(len(v) for v in _connections.values())
    print(f"Widget connected to stream '{stream_id}'. Total connections: {total}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if stream_id in _connections:
            try:
                _connections[stream_id].remove(websocket)
            except ValueError:
                pass
        print(f"Widget disconnected from stream '{stream_id}'.")
