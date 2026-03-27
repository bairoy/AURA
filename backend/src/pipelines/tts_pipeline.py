from typing import AsyncIterator
import asyncio
from src.events import VoiceAgentEvent
from src.cartesia_tts import CartesiaTTS
from src.utils import merge_async_iters


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:

    print("[PIPELINE] TTS STREAM STARTED")

    tts = CartesiaTTS()
    
    print("[PIPELINE] Pre-warming TTS connection...")
    await tts._ensure_connection()
    print("[PIPELINE] TTS connection ready")

    async def process_upstream() -> AsyncIterator[VoiceAgentEvent]:
        buffer: list[str] = []
        last_sentence_length = 0

        async for event in event_stream:
            print(f"[PIPELINE] UPSTREAM EVENT: {event.type}")
            yield event

            if event.type == "agent_chunk":
                print(f"[PIPELINE] AGENT TEXT: {event.text}")
                buffer.append(event.text)
                
                # Only send on REAL sentence endings
                if event.text.strip().endswith((".", "!", "?")):
                    text = "".join(buffer).strip()
                    if text:
                        print(f"[PIPELINE] SENDING TO TTS: '{text[:50]}...' ({len(text)} chars)")
                        await tts.send_text(text)
                        last_sentence_length = len(text)  # Track for next time
                    buffer = []

            if event.type == "agent_end" and buffer:
                text = "".join(buffer).strip()
                if text:
                    print(f"[PIPELINE] FINAL SEND TO TTS: '{text}'")
                    await tts.send_text(text)
                buffer = []

    try:
        async for event in merge_async_iters(
            process_upstream(),
            tts.receive_events(),
        ):
            if event.type == "tts_chunk":
                print(f"[PIPELINE] TTS AUDIO: {len(event.audio)} bytes")
            yield event
    except Exception as e:
        print(f"[PIPELINE] ERROR in tts_stream: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        print("[PIPELINE] TTS STREAM CLOSED")
        await tts.close()