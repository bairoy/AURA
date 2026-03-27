
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.websocket.handler import handle_websocket
from src.core.agent import get_checkpointer
from src.db.users import create_tables
from src.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    # Only DB tables + checkpointer at startup — fast, no MCP subprocess
    await create_tables()
    await get_checkpointer()
    print("✅ Server ready. Agent will initialize when user connects.")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
