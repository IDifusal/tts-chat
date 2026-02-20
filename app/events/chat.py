import re
import time
from typing import Dict, Any
from pathlib import Path

# Kick emotes: [emote:37226:KEKW] — skip TTS when message contains them
EMOTE_PATTERN = re.compile(r"\[emote:\d+:[^\]]+\]", re.IGNORECASE)
STICKER_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$", re.IGNORECASE)


from app.config import settings
from app.services.tts import get_tts
from app.routes.websocket import broadcast_to_stream
from app.logger import logger
from app.events.base import EventHandler


class ChatEventHandler(EventHandler):
    def __init__(self):
        self.tts = get_tts()
        self.last_message_time = {}
        self._last_spoken_text: str | None = None
        self._last_spoken_time: float = 0

    def should_process(self, event_data: Dict[str, Any]) -> bool:
        sender = event_data.get("sender", {})
        username = sender.get("username", "").lower()

        if username == "kickbot":
            return False

        return True

    def _check_cooldown(self, username: str) -> bool:
        now = time.time()
        last_time = self.last_message_time.get(username, 0)

        if now - last_time < settings.COOLDOWN_SECONDS:
            return False

        self.last_message_time[username] = now
        return True

    def _is_follower(self, event_data: Dict[str, Any]) -> bool:
        """
        Returns True if the sender has a qualifying badge.
        Kick includes sender.identity.badges in every chat message — no extra API call needed.
        The allowed badge types are controlled by TTS_ALLOWED_BADGES in config / .env.
        """
        allowed = {b.strip().lower() for b in settings.TTS_ALLOWED_BADGES.split(",") if b.strip()}

        sender = event_data.get("sender", {})
        identity = sender.get("identity", {})
        badges = identity.get("badges", [])

        for badge in badges:
            if badge.get("type", "").lower() in allowed:
                return True

        return False

    async def handle(self, event_data: Dict[str, Any], stream_id: str):
        if not self.should_process(event_data):
            return

        content = event_data.get("content", "")
        sender = event_data.get("sender", {})
        username = sender.get("username", "unknown")

        logger.info(f"{username}: {content}")

        if not self._check_cooldown(username):
            return

        # !sticker must be checked before the generic !s TTS command
        if settings.ENABLE_STICKERS and content.strip().lower().startswith("!sticker"):
            handled = await self._handle_sticker_command(content, username, stream_id)
            if handled:
                return

        # TTS command: !s <text>
        tts_prefix = settings.TTS_COMMAND + " "
        if settings.ENABLE_TTS and content.startswith(tts_prefix):
            tts_text = content[len(tts_prefix):].strip()

            if not tts_text:
                return

            if settings.TTS_FOLLOWERS_ONLY and not self._is_follower(event_data):
                logger.debug(f"TTS denied for '{username}': not a follower")
                return

            await self._handle_tts_message(tts_text, username, stream_id)
            return

        # Sound commands (!anything other than the TTS command)
        if content.startswith("!") and settings.ENABLE_SOUNDS:
            await self._handle_sound_command(content, username, stream_id)

    async def _handle_sound_command(self, content: str, username: str, stream_id: str):
        sound_name = content[1:].split()[0]
        sound_path = settings.SOUNDS_DIR / f"{sound_name}.mp3"

        if sound_path.exists():
            logger.info(f"Playing sound: {sound_name} (requested by {username})")

            await broadcast_to_stream(stream_id, {
                'type': 'sound_effect',
                'sound_name': sound_name,
                'audio_url': f"/static/sounds/{sound_name}.mp3",
                'username': username,
            })
        else:
            logger.warning(f"Sound not found: {sound_name}")

    def _find_sticker_assets(self, sticker_name: str) -> tuple[Path | None, Path | None]:
        sticker_dir = settings.STICKERS_DIR / sticker_name
        if not sticker_dir.exists():
            return None, None

        gif_path = sticker_dir / "sticker.gif"
        if not gif_path.exists():
            candidates = sorted(sticker_dir.glob("*.gif"))
            if not candidates:
                return None, None
            gif_path = candidates[0]

        sound_path: Path | None = None
        for ext in ("mp3", "wav", "ogg"):
            candidate = sticker_dir / f"sound.{ext}"
            if candidate.exists():
                sound_path = candidate
                break
        if sound_path is None:
            for ext in ("mp3", "wav", "ogg"):
                candidates = sorted(sticker_dir.glob(f"*.{ext}"))
                if candidates:
                    sound_path = candidates[0]
                    break

        return gif_path, sound_path

    async def _handle_sticker_command(self, content: str, username: str, stream_id: str) -> bool:
        parts = content.strip().split()
        if len(parts) < 2:
            logger.warning(f"Sticker command missing name (requested by {username})")
            return True

        sticker_name = parts[1].strip()
        if not STICKER_NAME_PATTERN.match(sticker_name):
            logger.warning(f"Invalid sticker name: {sticker_name!r} (requested by {username})")
            return True

        gif_path, sound_path = self._find_sticker_assets(sticker_name)
        if gif_path is None:
            logger.warning(f"Sticker not found: {sticker_name}")
            return True

        audio_url = None
        if sound_path is not None:
            audio_url = f"/static/stickers/{sticker_name}/{sound_path.name}"

        await broadcast_to_stream(stream_id, {
            "type": "sticker",
            "sticker_name": sticker_name,
            "gif_url": f"/static/stickers/{sticker_name}/{gif_path.name}",
            "audio_url": audio_url,
            "duration_ms": settings.STICKER_DURATION_MS,
            "username": username,
        })
        return True

    def _build_text_to_speak(self, content: str, username: str) -> str:
        prefix = (settings.TTS_PREFIX or "").replace("{username}", username)
        text = f"{prefix}{content}"
        if settings.TTS_MAX_CHARS > 0 and len(text) > settings.TTS_MAX_CHARS:
            text = text[: settings.TTS_MAX_CHARS]
        return text

    async def _handle_tts_message(self, content: str, username: str, stream_id: str):
        if len(content) < settings.MIN_MESSAGE_LENGTH:
            logger.debug(f"Message too short ({len(content)} chars), skipping")
            return

        if EMOTE_PATTERN.search(content):
            logger.debug(f"Message contains emote, skipping TTS: {content[:50]}...")
            return

        if len(content) > settings.MAX_MESSAGE_LENGTH:
            content = content[: settings.MAX_MESSAGE_LENGTH]

        normalized = content.strip().lower()
        if settings.TTS_SKIP_DUPLICATE_SECONDS > 0 and normalized:
            now = time.time()
            if (
                self._last_spoken_text == normalized
                and (now - self._last_spoken_time) < settings.TTS_SKIP_DUPLICATE_SECONDS
            ):
                logger.debug(f"Duplicate text in last {settings.TTS_SKIP_DUPLICATE_SECONDS}s, skipping TTS")
                return

        text_to_speak = self._build_text_to_speak(content, username)
        try:
            logger.info(f"Generating TTS for {username}: {content[:50]}...")
            audio_url, cached, gen_time = self.tts.generate(text_to_speak, username)

            if settings.TTS_SKIP_DUPLICATE_SECONDS > 0 and normalized:
                self._last_spoken_text = normalized
                self._last_spoken_time = time.time()

            await broadcast_to_stream(stream_id, {
                'type': 'tts_message',
                'username': username,
                'text': content,
                'audio_url': audio_url,
                'cached': cached,
                'generation_time_ms': gen_time,
            })

            logger.info(f"TTS generated: {audio_url} ({gen_time:.0f}ms, cached={cached})")

        except Exception as e:
            logger.error(f"TTS generation error: {e}", exc_info=True)
