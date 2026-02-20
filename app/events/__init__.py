from app.events.base import EventHandler
from app.events.chat import ChatEventHandler
from app.events.subscription import SubscriptionEventHandler
from app.events.follow import FollowEventHandler

EVENT_HANDLERS = {
    'App\\Events\\ChatMessageEvent': ChatEventHandler(),
    'App\\Events\\ChannelSubscriptionEvent': SubscriptionEventHandler(),
    'App\\Events\\FollowEvent': FollowEventHandler(),
}

async def handle_event(event_type: str, event_data: dict, stream_id: str):
    """Route event to the appropriate handler for the given stream."""
    handler = EVENT_HANDLERS.get(event_type)

    if handler:
        await handler.handle(event_data, stream_id)
