from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json


router = APIRouter()

active_connections: List[WebSocket] = []


async def broadcast_to_widgets(message: dict):
    """Send message to all connected widgets"""
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    
    for conn in disconnected:
        active_connections.remove(conn)


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for widgets"""
    await websocket.accept()
    active_connections.append(websocket)
    
    print(f"Widget connected. Total: {len(active_connections)}")
    
    try:
        while True:
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"Widget disconnected. Total: {len(active_connections)}")
