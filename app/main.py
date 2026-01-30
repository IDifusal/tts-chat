from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.routes import api, websocket
from app.services.kick_listener import KickListener


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown"""
    print("Starting Kick TTS Bot...")
    
    kick_listener = KickListener(settings.KICK_CHANNEL)
    asyncio.create_task(kick_listener.start())
    
    yield
    
    print("Shutting down Kick TTS Bot...")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main control panel"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "channel": settings.KICK_CHANNEL}
    )


@app.get("/widget", response_class=HTMLResponse)
async def widget(request: Request):
    """Widget for OBS"""
    return templates.TemplateResponse(
        "widget.html",
        {"request": request}
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "channel": settings.KICK_CHANNEL}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
