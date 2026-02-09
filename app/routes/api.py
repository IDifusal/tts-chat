from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import re
from pathlib import Path

from app.models import TTSRequest, TTSResponse, SoundEffectRequest
from app.services.tts import get_tts
from app.services.sound_service import get_sound_service
from app.routes.websocket import broadcast_to_widgets
from app.config import settings

router = APIRouter()

STICKER_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$", re.IGNORECASE)


class TestEventRequest(BaseModel):
    username: str = "test_user"

class TestStickerRequest(BaseModel):
    sticker_name: str
    username: str = "test_user"
    duration_ms: int | None = None


def _find_sticker_assets(sticker_name: str) -> tuple[Path | None, Path | None]:
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


@router.post("/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate TTS audio from text"""
    try:
        username = request.username or "api"
        text_to_speak = f"{username} dice: {request.text}"
        tts = get_tts()
        audio_url, cached, gen_time = tts.generate(
            text_to_speak,
            username,
            request.use_cache
        )
        
        await broadcast_to_widgets({
            'type': 'tts_message',
            'username': username,
            'text': request.text,
            'audio_url': audio_url,
            'cached': cached,
            'generation_time_ms': gen_time
        })
        
        return TTSResponse(
            audio_url=audio_url,
            cached=cached,
            generation_time_ms=gen_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/elevenlabs/voices")
async def list_elevenlabs_voices():
    """
    Lista voces disponibles en tu cuenta de ElevenLabs.
    En plan Free solo puedes usar por API voces con 'free' en available_for_tiers
    o voces propias (clonadas). Usa un voice_id de esta lista en ELEVEN_LABS_VOICE_ID.
    """
    from app.config import settings
    if not settings.ELEVEN_LABS_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="ELEVEN_LABS_API_KEY no configurada. Añádela en .env para listar voces.",
        )
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=settings.ELEVEN_LABS_API_KEY)
        resp = client.voices.search()
        # SDK devuelve objeto con .voices (GET /v2/voices)
        voices = getattr(resp, "voices", resp) if not isinstance(resp, list) else resp
        out = []
        for v in (voices or []):
            voice_id = getattr(v, "voice_id", None) or getattr(v, "id", None)
            name = getattr(v, "name", None) or ""
            tiers = getattr(v, "available_for_tiers", None) or []
            # Algunas voces tienen sharing.free_users_allowed
            free_ok = "free" in (tiers if isinstance(tiers, list) else [])
            if hasattr(v, "sharing") and v.sharing:
                free_ok = free_ok or getattr(v.sharing, "free_users_allowed", False)
            out.append({
                "voice_id": voice_id,
                "name": name,
                "available_for_tiers": tiers,
                "usable_on_free_tier": free_ok,
            })
        return {"voices": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sounds", response_model=List[str])
async def list_sounds():
    """List available sound effects"""
    sound_service = get_sound_service()
    return sound_service.get_available_sounds()


@router.post("/play-sound")
async def play_sound(request: SoundEffectRequest):
    """Play a sound effect"""
    sound_service = get_sound_service()
    
    if not sound_service.sound_exists(request.sound_name):
        raise HTTPException(status_code=404, detail="Sound not found")
    
    sound_url = sound_service.get_sound_url(request.sound_name)
    
    await broadcast_to_widgets({
        'type': 'sound_effect',
        'sound_name': request.sound_name,
        'audio_url': sound_url,
        'username': request.username or 'api'
    })
    
    return {"status": "ok", "sound_url": sound_url}


@router.post("/test/subscription")
async def test_subscription(request: TestEventRequest):
    """Test subscription event"""
    await broadcast_to_widgets({
        'type': 'subscription',
        'username': request.username,
        'user_id': 12345,
        'channel_id': 67890
    })
    return {"status": "ok", "event": "subscription", "username": request.username}


@router.post("/test/follow")
async def test_follow(request: TestEventRequest):
    """Test follow event"""
    await broadcast_to_widgets({
        'type': 'follow',
        'username': request.username,
        'followed': 'test_channel'
    })
    return {"status": "ok", "event": "follow", "username": request.username}


@router.post("/test/sticker")
async def test_sticker(request: TestStickerRequest):
    sticker_name = request.sticker_name.strip()
    if not STICKER_NAME_PATTERN.match(sticker_name):
        raise HTTPException(status_code=400, detail="Invalid sticker_name")

    gif_path, sound_path = _find_sticker_assets(sticker_name)
    if gif_path is None:
        raise HTTPException(status_code=404, detail="Sticker not found")

    audio_url = None
    if sound_path is not None:
        audio_url = f"/static/stickers/{sticker_name}/{sound_path.name}"

    duration_ms = request.duration_ms if request.duration_ms is not None else settings.STICKER_DURATION_MS

    await broadcast_to_widgets({
        "type": "sticker",
        "sticker_name": sticker_name,
        "gif_url": f"/static/stickers/{sticker_name}/{gif_path.name}",
        "audio_url": audio_url,
        "duration_ms": duration_ms,
        "username": request.username or "api",
    })
    return {"status": "ok", "event": "sticker", "sticker_name": sticker_name, "duration_ms": duration_ms, "audio_url": audio_url}
