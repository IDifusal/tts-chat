from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from app.models import TTSRequest, TTSResponse, SoundEffectRequest
from app.services.tts import get_tts
from app.services.sound_service import get_sound_service
from app.routes.websocket import broadcast_to_widgets

router = APIRouter()


class TestEventRequest(BaseModel):
    username: str = "test_user"


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
