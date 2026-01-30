from abc import ABC, abstractmethod
from typing import Dict, Any


class EventHandler(ABC):
    """Base class for all event handlers"""
    
    @abstractmethod
    async def handle(self, event_data: Dict[str, Any]):
        """Process the event data"""
        pass
    
    @abstractmethod
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        """Check if this event should be processed"""
        pass
