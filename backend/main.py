from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


from src.websocket.handler import handle_websocket



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)


# frontend mount
root = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(root), html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
