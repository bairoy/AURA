import asyncio
import os
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI
from src.events import TTSChunkEvent


class OpenAITTS:
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice: str = "alloy",
        model: str = "gpt-4o-mini-tts",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY missing")

        self.client = AsyncOpenAI(api_key=self.api_key)

        self.voice = voice
        self.model = model

        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._closed = False

    async def send_text(self, text: Optional[str]):
        if not text:
            return

        async def _generate():
            async with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="pcm",   # CORRECT PARAMETER
            ) as response:

                async for chunk in response.iter_bytes():
                    await self._queue.put(chunk)

        asyncio.create_task(_generate())

    async def receive_events(self) -> AsyncIterator[TTSChunkEvent]:
        while not self._closed:
            chunk = await self._queue.get()
            yield TTSChunkEvent.create(chunk)

    async def close(self):
        self._closed = True
