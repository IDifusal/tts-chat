from typing import Dict, Any

from app.routes.websocket import broadcast_to_widgets
from app.logger import logger
from app.events.base import EventHandler


class FollowEventHandler(EventHandler):
    """Handle new follower events"""
    
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        """Process if we have follower information"""
        # Event can have either 'username' or 'follower' object
        return (
            event_data.get("username") is not None or
            event_data.get("follower") is not None
        )
    
    async def handle(self, event_data: Dict[str, Any]):
        """Process follow event and show alert"""
        
        # Extract username from different possible structures
        username = event_data.get("username")
        
        if not username:
            follower = event_data.get("follower", {})
            username = follower.get("username", "unknown")
        
        followed_name = event_data.get("followed", {}).get("username", "")
        
        logger.info(f"New follower: {username} → {followed_name}")
        
        # Broadcast to widgets
        await broadcast_to_widgets({
            'type': 'follow',
            'username': username,
            'followed': followed_name
        })
