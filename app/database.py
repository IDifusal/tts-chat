import aiosqlite
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/streams.db")


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS streams (
                stream_id  TEXT PRIMARY KEY,
                channel    TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()


async def get_all_streams() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT stream_id, channel, created_at FROM streams ORDER BY created_at"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_stream(stream_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT stream_id, channel, created_at FROM streams WHERE stream_id = ?",
            (stream_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_stream(stream_id: str, channel: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO streams (stream_id, channel) VALUES (?, ?)",
            (stream_id, channel),
        )
        await db.commit()


async def update_stream_channel(stream_id: str, channel: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE streams SET channel = ? WHERE stream_id = ?",
            (channel, stream_id),
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
