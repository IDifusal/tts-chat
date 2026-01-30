"""
Template for creating new event handlers.
Copy this file and rename it to match your event type.
"""

from typing import Dict, Any

from app.config import settings
from app.routes.websocket import broadcast_to_widgets
from app.logger import logger
from app.events.base import EventHandler


class TemplateEventHandler(EventHandler):
    """Handle [EVENT_TYPE] events"""
    
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        """
        Determine if this event should be processed.
        Return False to skip this event.
        """
        # Example: Check if required fields exist
        # if not event_data.get("required_field"):
        #     return False
        
        return True
    
    async def handle(self, event_data: Dict[str, Any]):
        """
        Process the event data and broadcast to widgets.
        """
        # Extract data from event_data
        # Example:
        # username = event_data.get("username", "unknown")
        # amount = event_data.get("amount", 0)
        
        logger.info(f"Processing [EVENT_TYPE]: {event_data}")
        
        # Broadcast to widgets
        await broadcast_to_widgets({
            'type': 'your_event_type',  # Must match widget.html handler
            'username': 'username',
            # Add more fields as needed
        })
