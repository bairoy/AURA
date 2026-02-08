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
    print("[WEBSOCKET] Client connected")

    output_stream = pipeline.atransform(
        websocket_audio_stream(websocket)
    )

    event_count = {"total": 0, "audio": 0}
    
    async for event in output_stream:
        event_count["total"] += 1
        if event.type == "tts_chunk":
            event_count["audio"] += 1
            print(f"[WEBSOCKET] Sending audio event #{event_count['audio']}, size: {len(event.audio)} bytes")
        
        try:
            event_dict = event_to_dict(event)
            print(f"[WEBSOCKET] Sending event: {event.type} (total: {event_count['total']})")
            await websocket.send_json(event_dict)
        except Exception as e:
            print(f"[WEBSOCKET] Error sending event: {e}")
            break
    
    print(f"[WEBSOCKET] Stream ended. Sent {event_count['total']} events ({event_count['audio']} audio chunks)")
