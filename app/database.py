import aiosqlite
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/streams.db")


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS streams (
                stream_id           TEXT PRIMARY KEY,
                channel             TEXT NOT NULL,
                tts_backend         TEXT NOT NULL DEFAULT 'elevenlabs',
                elevenlabs_voice_id TEXT,
                created_at          TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

        # Migrate existing DBs that don't have the voice columns yet
        for col, definition in [
            ("tts_backend", "TEXT NOT NULL DEFAULT 'elevenlabs'"),
            ("elevenlabs_voice_id", "TEXT"),
        ]:
            try:
                await db.execute(f"ALTER TABLE streams ADD COLUMN {col} {definition}")
                await db.commit()
            except Exception:
                pass  # Column already exists


async def get_all_streams() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT stream_id, channel, tts_backend, elevenlabs_voice_id, created_at FROM streams ORDER BY created_at"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_stream(stream_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT stream_id, channel, tts_backend, elevenlabs_voice_id, created_at FROM streams WHERE stream_id = ?",
            (stream_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_stream(
    stream_id: str,
    channel: str,
    tts_backend: str = "elevenlabs",
    elevenlabs_voice_id: str | None = None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO streams (stream_id, channel, tts_backend, elevenlabs_voice_id)
               VALUES (?, ?, ?, ?)""",
            (stream_id, channel, tts_backend, elevenlabs_voice_id),
        )
        await db.commit()


async def update_stream(
    stream_id: str,
    channel: str | None = None,
    tts_backend: str | None = None,
    elevenlabs_voice_id: str | None = None,
) -> bool:
    """Update any combination of fields on a stream row."""
    fields, values = [], []

    if channel is not None:
        fields.append("channel = ?")
        values.append(channel)
    if tts_backend is not None:
        fields.append("tts_backend = ?")
        values.append(tts_backend)
    if elevenlabs_voice_id is not None:
        fields.append("elevenlabs_voice_id = ?")
        values.append(elevenlabs_voice_id)

    if not fields:
        return True

    values.append(stream_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"UPDATE streams SET {', '.join(fields)} WHERE stream_id = ?",
            values,
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_stream(stream_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM streams WHERE stream_id = ?", (stream_id,)
        )
        await db.commit()
        return cursor.rowcount > 0
