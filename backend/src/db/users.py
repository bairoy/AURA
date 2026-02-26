import os
from uuid import uuid4
from typing import Optional
import psycopg
from dotenv import load_dotenv

load_dotenv()


def _dsn() -> str:
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB', 'aura')}"
    )


async def create_tables() -> None:
    """Create users and threads tables if they don't exist."""
    async with await psycopg.AsyncConnection.connect(_dsn(), autocommit=True) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                thread_id TEXT UNIQUE NOT NULL,
                label TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    print("✅ Users and threads tables ready")


# ── User CRUD ──────────────────────────────────────────────────────────────────

async def create_user(username: str, password_hash: str) -> dict:
    async with await psycopg.AsyncConnection.connect(_dsn(), autocommit=True) as conn:
        row = await (await conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username, created_at",
            (username, password_hash),
        )).fetchone()
    return {"id": str(row[0]), "username": row[1], "created_at": row[2]}


async def get_user_by_username(username: str) -> Optional[dict]:
    async with await psycopg.AsyncConnection.connect(_dsn()) as conn:
        row = await (await conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        )).fetchone()
    if not row:
        return None
    return {"id": str(row[0]), "username": row[1], "password_hash": row[2]}


# ── Thread CRUD ────────────────────────────────────────────────────────────────

async def create_thread(user_id: str, label: Optional[str] = None) -> dict:
    thread_id = str(uuid4())
    label = label or f"Conversation {thread_id[:8]}"
    async with await psycopg.AsyncConnection.connect(_dsn(), autocommit=True) as conn:
        row = await (await conn.execute(
            """INSERT INTO threads (user_id, thread_id, label)
               VALUES (%s, %s, %s)
               RETURNING id, thread_id, label, created_at""",
            (user_id, thread_id, label),
        )).fetchone()
    return {
        "id": str(row[0]),
        "thread_id": row[1],
        "label": row[2],
        "created_at": row[3],
    }


async def get_user_threads(user_id: str) -> list[dict]:
    """Return all threads for a user, newest first."""
    async with await psycopg.AsyncConnection.connect(_dsn()) as conn:
        rows = await (await conn.execute(
            "SELECT id, thread_id, label, created_at FROM threads WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )).fetchall()
    return [
        {"id": str(r[0]), "thread_id": r[1], "label": r[2], "created_at": r[3]}
        for r in rows
    ]


async def get_latest_thread(user_id: str) -> Optional[dict]:
    """Return the most recent thread for a user."""
    threads = await get_user_threads(user_id)
    return threads[0] if threads else None
