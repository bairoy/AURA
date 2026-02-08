from typing import AsyncIterator
from fastapi import WebSocket

from src.pipelines.full_pipeline import pipeline
from src.events import event_to_dict


async def websocket_audio_stream(websocket: WebSocket) -> AsyncIterator[bytes]:

    try:
        while True:
            msg = await websocket.receive()

            if msg.get("type") == "websocket.receive" and "bytes" in msg:
                yield msg["bytes"]

            elif msg.get("type") == "websocket.disconnect":
                break
    except RuntimeError as e:
        print("WebSocket stopped:", e)


async def handle_websocket(websocket: WebSocket):
    await websocket.accept()

    output_stream = pipeline.atransform(
        websocket_audio_stream(websocket)
    )

    async for event in output_stream:
        await websocket.send_json(event_to_dict(event))
