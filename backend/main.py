# from dotenv import load_dotenv
# load_dotenv()

# from contextlib import asynccontextmanager
# from pathlib import Path

# import uvicorn
# from fastapi import FastAPI, WebSocket
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# from src.websocket.handler import handle_websocket
# from src.core.agent import get_agent_with_checkpointer
# from src.db.users import create_tables
# from src.api.auth import router as auth_router


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("🚀 Starting up...")
#     # 1. Create DB tables (users, threads) if they don't exist
#     await create_tables()
#     # 2. Pre-initialize agent + checkpointer so first user has no delay
#     print("🚀 Pre-initializing agent and checkpointer...")
#     await get_agent_with_checkpointer()
#     print("✅ Agent ready. Server accepting connections.")
#     yield


# app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://localhost:8000"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Auth REST endpoints: /auth/register, /auth/login, /auth/threads
# app.include_router(auth_router)


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await handle_websocket(websocket)


# # Frontend
# root = Path(__file__).resolve().parent.parent / "frontend"
# app.mount("/", StaticFiles(directory=str(root), html=True), name="frontend")


# if __name__ == "__main__":
#     uvicorn.run("main:app", port=8000, reload=True)



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
