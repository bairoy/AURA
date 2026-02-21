import os
import urllib.parse
from dotenv import load_dotenv 
load_dotenv()

import psycopg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def init_checkpointer() -> AsyncPostgresSaver:
    """Initialize LangGraph checkpointing with native async Postgres connection."""

    db_user = os.getenv("POSTGRES_USER")
    db_pass = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB", "aura")  # default to 'aura'
    
    # Connection string for psycopg (async)
    dsn = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    print(f"🔗 Connecting to Postgres for LangGraph checkpoints...")

    # Create async connection with autocommit
    conn = await psycopg.AsyncConnection.connect(dsn, autocommit=True)
    print(f"✅ Connected to Postgres")

    # Create checkpointer
    saver = AsyncPostgresSaver(conn)
    print("🔧 Setting up checkpointer tables...")
    await saver.setup()
    print("✅ Checkpointer ready")

    return saver

