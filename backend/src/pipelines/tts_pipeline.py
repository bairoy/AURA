# from typing import AsyncIterator 
# from src.events import VoiceAgentEvent
# from src.cartesia_tts import CartesiaTTS
# from src.utils import merge_async_iters

# async def tts_stream(
#     event_stream: AsyncIterator[VoiceAgentEvent],
# )-> AsyncIterator[VoiceAgentEvent]:
#   """
#   args:
#    event_stream: An asyncc iterator of upstream voice agent events
#   yields:
#   all upstream events plus tts_chunk events for synthesized audio

#   """
#   tts = CartesiaTTS()

#   async def process_upstream()->AsyncIterator[VoiceAgentEvent]:
#     buffer:list[str] = []
#     async for event in event_stream:
#       yield event 
#       if event.type == "agent_chunk":
#         buffer.append(event.text)
#       if event.type == "agent_end":
#         await tts.send_text("".join(buffer))
#         buffer = []

#   try:
#     async for event in merge_async_iters(process_upstream(),tts.receive_events()):
#       yield event
#   finally:
#     await tts.close()

# from src.openai_tts import OpenAITTS as CartesiaTTS
from typing import AsyncIterator
from src.events import VoiceAgentEvent
from src.cartesia_tts import CartesiaTTS
from src.utils import merge_async_iters



async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:

    print("[PIPELINE] TTS STREAM STARTED")

    tts = CartesiaTTS()

    async def process_upstream() -> AsyncIterator[VoiceAgentEvent]:
        buffer: list[str] = []

        async for event in event_stream:
            print(f"[PIPELINE] UPSTREAM EVENT: {event.type}")
            yield event

            if event.type == "agent_chunk":
                print(f"[PIPELINE] AGENT TEXT: {event.text}")
                buffer.append(event.text)

                if event.text.strip().endswith((".", "!", "?")):
                    text = "".join(buffer)
                    print(f"[PIPELINE] SENDING TEXT TO TTS: '{text}'")
                    await tts.send_text(text)
                    buffer = []

            if event.type == "agent_end" and buffer:
                text = "".join(buffer)
                print(f"[PIPELINE] FINAL SEND TO TTS: '{text}'")
                await tts.send_text(text)
                buffer = []

    try:
        async for event in merge_async_iters(
            process_upstream(),
            tts.receive_events(),
        ):
            print(f"[PIPELINE] TTS EVENT RETURNED: {event.type}")
            yield event
    except Exception as e:
        print(f"[PIPELINE] ERROR in tts_stream: {e}")
        raise
    finally:
        print("[PIPELINE] TTS STREAM CLOSED")
        await tts.close()
