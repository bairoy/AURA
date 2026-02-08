from typing import AsyncIterator
from src.utils import merge_async_iters
from src.events import VoiceAgentEvent
from src.assemblyai_stt import AssemblyAISTT
import asyncio
import contextlib



async def stt_stream(
    audio_stream: AsyncIterator[bytes],
) -> AsyncIterator[VoiceAgentEvent]:

    stt = AssemblyAISTT(sample_rate=16000)

    async def send_audio():
        try:
            async for audio_chunk in audio_stream:
                print("AUDIO BYTES:", len(audio_chunk))
                await stt.send_audio(audio_chunk)
        except asyncio.CancelledError:
            pass

    send_task = asyncio.create_task(send_audio())

    try:
        async for event in stt.receive_events():
            yield event
    finally:
        send_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await send_task
        await stt.close()
