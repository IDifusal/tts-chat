from fastapi import APIRouter, HTTPException
from typing import List

from app.models import TTSRequest, TTSResponse, SoundEffectRequest
from app.services.piper_tts import get_tts
from app.services.sound_service import get_sound_service
from app.routes.websocket import broadcast_to_widgets

router = APIRouter()


@router.post("/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate TTS audio from text"""
    try:
        tts = get_tts()
        audio_url, cached, gen_time = tts.generate(
            request.text,
            request.username,
            request.use_cache
        )
        
        await broadcast_to_widgets({
            'type': 'tts_message',
            'username': request.username or 'api',
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
