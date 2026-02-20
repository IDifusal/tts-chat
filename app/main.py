from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.database import init_db, get_all_streams, get_stream
from app.routes import api, websocket
from app.routes import streams as streams_router
from app.services.stream_manager import stream_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Kick TTS Bot...")

    await init_db()

    all_streams = await get_all_streams()
    if all_streams:
        await stream_manager.start_all(all_streams)
        print(f"Loaded {len(all_streams)} stream(s) from database.")
    else:
        print("No streams in database. Add one via POST /api/streams")

    yield

    print("Shutting down Kick TTS Bot...")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(streams_router.router, prefix="/api", tags=["streams"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/{stream_id}", response_class=HTMLResponse)
async def stream_widget(request: Request, stream_id: str):
    """Widget page scoped to a specific stream."""
    stream = await get_stream(stream_id)
    if stream is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Stream '{stream_id}' not found. Add it via POST /api/streams"},
        )
    return templates.TemplateResponse(
        "widget.html",
        {"request": request, "stream_id": stream_id, "channel": stream["channel"]},
    )


@app.get("/{stream_id}/widget", response_class=HTMLResponse)
async def stream_widget_explicit(request: Request, stream_id: str):
    """Same as /{stream_id} — explicit /widget suffix."""
    return await stream_widget(request, stream_id)


@app.get("/health")
async def health():
    """Health check"""
    streams = await get_all_streams()
    running = stream_manager.get_running_streams()
    return {
        "status": "ok",
        "streams": [
            {"stream_id": s["stream_id"], "channel": s["channel"], "running": s["stream_id"] in running}
            for s in streams
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
