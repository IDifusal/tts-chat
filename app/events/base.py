from abc import ABC, abstractmethod
from typing import Dict, Any


class EventHandler(ABC):
    """Base class for all event handlers"""
    
    @abstractmethod
    async def handle(self, event_data: Dict[str, Any], stream_id: str):
        """Process the event data for the given stream."""
        pass
    
    @abstractmethod
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        """Check if this event should be processed"""
        pass
