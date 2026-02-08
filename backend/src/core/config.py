import os
import urllib.parse
from dotenv import load_dotenv 
load_dotenv()


import psycopg

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver





async def init_checkpointer() -> AsyncPostgresSaver:
    """Initialize LangGraph checkpointing with native async Postgres connection."""

    db_user = os.getenv("POSTGRES_USER")
    db_pass = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD"))
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    

    dsn = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/aura"
    
    print(f"🔗 Connecting to Postgres for LangGraph checkpoints: {dsn}")

    # ✅ Enable autocommit to allow concurrent index creation
    conn = await psycopg.AsyncConnection.connect(
        f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/aura",
        autocommit=True
    )
    print(f"🔗 Connected to Postgres for LangGraph checkpoints: {conn}")

    # ✅ Pass the native connection to LangGraph
    saver = AsyncPostgresSaver(conn)
    print("saver initialized here")
    await saver.setup()
    print("saver setup")

    
    return saver