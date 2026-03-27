from typing import AsyncIterator
from fastapi import WebSocket

from src.auth.jwt import decode_token
from src.db.users import create_thread
from src.core.agent import create_session_agent
from src.pipelines.stt_pipeline import stt_stream
from src.pipelines.tts_pipeline import tts_stream
from src.pipelines.agent_pipeline import agent_stream
from src.events import event_to_dict


async def websocket_audio_stream(websocket: WebSocket) -> AsyncIterator[bytes]:
    try:
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.receive" and "bytes" in msg:
                yield msg["bytes"]
            elif msg.get("type") == "websocket.disconnect":
                break
    except RuntimeError:
        pass


async def handle_websocket(websocket: WebSocket):
    # ── 1. Auth ────────────────────────────────────────────────────────────────
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user = decode_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # ── 2. Thread ──────────────────────────────────────────────────────────────
    thread_id = websocket.query_params.get("thread_id")
    if not thread_id:
        new_thread = await create_thread(user["user_id"])
        thread_id = new_thread["thread_id"]
        print(f"[WS] New thread {thread_id} for {user['username']}")
    else:
        print(f"[WS] Continuing thread {thread_id} for {user['username']}")

    await websocket.accept()

    # ── 3. Initialize agent for this session ───────────────────────────────────
    print(f"[WS] Initializing agent for {user['username']}...")
    agent = await create_session_agent()

    # ── 4. Chain streams directly (no RunnableGenerator) ──────────────────────
    audio_stream = websocket_audio_stream(websocket)
    stt_events   = stt_stream(audio_stream)
    agent_events = agent_stream(stt_events, agent=agent, thread_id=thread_id)
    tts_events   = tts_stream(agent_events)

    # ── 5. Send all events to frontend ────────────────────────────────────────
    event_count = {"total": 0, "audio": 0}

    async for event in tts_events:
        event_count["total"] += 1
        if event.type == "tts_chunk":
            event_count["audio"] += 1
        try:
            await websocket.send_json(event_to_dict(event))
        except Exception as e:
            print(f"[WS] Send error: {e}")
            break

    print(
        f"[WS] Session ended. User: {user['username']}, Thread: {thread_id}, "
        f"Events: {event_count['total']} ({event_count['audio']} audio)"
    )
