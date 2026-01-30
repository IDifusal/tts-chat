from typing import Dict, Any
import aiohttp

from app.config import settings
from app.routes.websocket import broadcast_to_widgets
from app.logger import logger
from app.events.base import EventHandler


class SubscriptionEventHandler(EventHandler):
    """Handle subscription events"""
    
    def should_process(self, event_data: Dict[str, Any]) -> bool:
        # Always process subscription events
        return True
    
    async def handle(self, event_data: Dict[str, Any]):
        # Get user IDs from the event
        user_ids = event_data.get("user_ids", [])
        channel_id = event_data.get("channel_id")
        
        if not user_ids:
            logger.warning("Subscription event with no user_ids")
            return
        
        logger.info(f"New subscription(s): {len(user_ids)} user(s)")
        
        # Fetch user information for each subscriber
        for user_id in user_ids:
            try:
                username = await self._get_username(user_id)
                
                if username:
                    logger.info(f"New subscriber: {username} (ID: {user_id})")
                    
                    # Broadcast subscription event to widgets
                    await broadcast_to_widgets({
                        'type': 'subscription',
                        'username': username,
                        'user_id': user_id,
                        'channel_id': channel_id
                    })
                
            except Exception as e:
                logger.error(f"Error processing subscription for user {user_id}: {e}")
    
    async def _get_username(self, user_id: int) -> str:
        """Fetch username from Kick API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"https://kick.com/api/v2/users/{user_id}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('username', f'User_{user_id}')
                    else:
                        logger.warning(f"Could not fetch user {user_id}: {response.status}")
                        return f"User_{user_id}"
        
        except Exception as e:
            logger.error(f"Error fetching username for {user_id}: {e}")
            return f"User_{user_id}"
