from app.events.chat import ChatEventHandler
from app.events.subscription import SubscriptionEventHandler
from app.events.follow import FollowEventHandler


def make_handlers(tts) -> dict:
    """
    Build a fresh set of event handlers for one stream.
    Each KickListener calls this so ChatEventHandler gets its own TTS instance.
    """
    return {
        'App\\Events\\ChatMessageEvent': ChatEventHandler(tts=tts),
        'App\\Events\\ChannelSubscriptionEvent': SubscriptionEventHandler(),
        'App\\Events\\FollowEvent': FollowEventHandler(),
    }


async def handle_event(event_type: str, event_data: dict, stream_id: str, handlers: dict):
    """Route an event to the appropriate handler."""
    handler = handlers.get(event_type)
    if handler:
        await handler.handle(event_data, stream_id)
