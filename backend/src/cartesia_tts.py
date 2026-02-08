# import asyncio 
# import base64 
# import contextlib 
# import json 
# import os 
# import time 
# from typing import AsyncIterator, Literal, Optional 

# import websockets 
# from websockets.client import WebSocketClientProtocol 

# from src.events import TTSChunkEvent 

# class CartesiaTTS:
#   _ws: Optional[WebSocketClientProtocol]
#   _connection_signal: asyncio.Event
#   _close_signal:asyncio.Event 

#   def __init__(
#       self,
#       api_key: Optional[str] = None,
#       voice_id: str = "f6ff7c0c-e396-40a9-a70b-f7607edb6937",
#       model_id: str = "sonic-3",
#       sample_rate: int = 24000,
#       encoding: Literal["pcm_s16le","pcm_f32le","pcm_mulaw","pcm_alaw"]="pcm_s16le",
#       language:str = "en",
#       cartesia_version:str = "2025-04-16",
#   ):
#     self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
#     if not self.api_key:
#       raise ValueError("Cartesia API key is required")
    
#     self.voice_id = voice_id = voice_id
#     self.model_id = model_id
#     self.sample_rate = sample_rate 
#     self.encoding = encoding
#     self.language = language 
#     self.cartesia_version = cartesia_version
#     self._ws = None 
#     self._connection_signal = asyncio.Event()
#     self._close_signal = asyncio.Event()
#     self._context_counter = 0

#   def _generate_context_id(self)->str:
#     timestamp = int(time.time()*1000)
#     counter = self._context_counter
#     self._context_counter += 1
#     return f"ctx_{timestamp}_{counter}"
  
#   async def send_text(self,text:Optional[str])-> None:
#     if text is None:
#       return 
#     if not text.strip():
#       return 
#     ws = await self._ensure_connection()

#     payload = {
#       "model_id":self.model_id,
#       "transcript":text,
#       "voice":{
#         "mode":"id",
#         "id":self.voice_id,
#       },
#       "output_format":{
#         "container":"raw",
#         "encoding":self.encoding,
#         "sample_rate":self.sample_rate,
#       },
#       "language":self.language,
#       "context_id":self._generate_context_id(),
#     }
#     await ws.send(json.dumps(payload))

#   async def receive_events(self)->AsyncIterator[TTSChunkEvent]:
#     while not self._close_signal.is_set():
#       _, pending = await asyncio.wait(
#         [
#           asyncio.create_task(self._close_signal.wait()),
#           asyncio.create_task(self._connection_signal.wait()),
#         ],
#         return_when=asyncio.FIRST_COMPLETED,
#       )
#       with contextlib.suppress(asyncio.CancelledError):
#         for task in pending:
#           task.cancel()
#       if self._close_signal.is_set():
#         break 

#       if self._ws and self._ws.close_code is None:
#         self._connection_signal.clear()
#         try:
#           async for raw_message in self._ws:
#             try:
#               message = json.loads(raw_message)
#               if "data" in message and message["data"] is not None:
#                 audio_chunk = base64.b64decode(message["data"])
#                 if audio_chunk:
#                   yield TTSChunkEvent.create(audio_chunk)
#               if message.get("done"):
#                 break 
#               if "error" in message and message["error"]:
#                 print(f"[DEBUG] Cartesia error: {message['error']}")
#                 break 
#             except json.JSONDecodeError as e:
#               print(f"[DEBUG] Cartesia JSON decode error: {e}")
#               continue 
#         except websockets.exceptions.ConnectionClosed:
#           print("Catesia: WebSocket connection closed")
#         finally:
#           if self._ws and self._ws.close_code is None:
#             await self._ws.close()
#           self._ws = None 
#   async def close(self)-> None:
#     if self._ws and self._ws.close_code is None:
#       await self._ws.close()
#     self._ws = None
#     self._close_signal.set()

#   async def _ensure_connection(self)-> WebSocketClientProtocol:
#     if self._close_signal.is_set():
#       raise RuntimeError(
#         "CatesiaTTS tried establishing a connection after it was closed"
#       )
#     if self._ws and self._ws.close_code is None:
#       return self._ws
    
#     url = (
#       f"wss://api.cartesia.ai/tts/websocket"
#       f"?api_key={self.api_key}&cartesia_version={self.cartesia_version}"
#     )
#     self._ws = await websockets.connect(url)
#     self._connection_signal.set()
#     return self._ws 
  

import asyncio
import base64
import json
import os
import time
from typing import AsyncIterator, Literal, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from src.events import TTSChunkEvent


class CartesiaTTS:
    _ws: Optional[WebSocketClientProtocol]

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: str = "f6ff7c0c-e396-40a9-a70b-f7607edb6937",
        model_id: str = "sonic-3",
        sample_rate: int = 24000,
        encoding: Literal["pcm_s16le", "pcm_f32le", "pcm_mulaw", "pcm_alaw"] = "pcm_s16le",
        language: str = "en",
        cartesia_version: str = "2025-04-16",
    ):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            raise ValueError("Cartesia API key is required")

        self.voice_id = voice_id
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.encoding = encoding
        self.language = language
        self.cartesia_version = cartesia_version

        self._ws = None
        self._connection_signal = asyncio.Event()
        self._close_signal = asyncio.Event()
        self._context_counter = 0

    def _generate_context_id(self) -> str:
        timestamp = int(time.time() * 1000)
        counter = self._context_counter
        self._context_counter += 1
        return f"ctx_{timestamp}_{counter}"

    async def send_text(self, text: Optional[str]) -> None:
        if not text or not text.strip():
            print("[TTS DEBUG] Skipping empty text")
            return

        print(f"[TTS DEBUG] Sending text to Cartesia: {text[:100]}")
        ws = await self._ensure_connection()
        print("[TTS DEBUG] Got WebSocket connection")

        payload = {
            "model_id": self.model_id,
            "text": text,
            "voice": {
                "mode": "id",
                "id": self.voice_id,
            },
            "output_format": {
                "container": "raw",
                "encoding": self.encoding,
                "sample_rate": self.sample_rate,
            },
            "language": self.language,
        }

        print(f"[TTS DEBUG] Sending payload to Cartesia: {payload}")
        await ws.send(json.dumps(payload))
        print("[TTS DEBUG] Text sent to Cartesia")

    async def receive_events(self) -> AsyncIterator[TTSChunkEvent]:
        while not self._close_signal.is_set():

            # wait until connection exists
            if not self._ws or self._ws.close_code is not None:
                print("[TTS DEBUG] Waiting for connection...")
                # Clear and wait for the connection signal
                self._connection_signal.clear()
                print("[TTS DEBUG] Cleared signal, now waiting...")
                await self._connection_signal.wait()
                print("[TTS DEBUG] Connection signal received, connection should be ready")
                # Small delay to ensure connection is fully ready
                await asyncio.sleep(0.1)

            ws = self._ws
            if not ws:
                print("[TTS DEBUG] Connection not ready yet, sleeping...")
                await asyncio.sleep(0.05)
                continue

            print("[TTS DEBUG] Starting to receive from Cartesia...")
            try:
                async for raw_message in ws:
                    try:
                        message = json.loads(raw_message)
                        print(f"[TTS DEBUG] Cartesia response received: {str(message)[:200]}")

                        if "data" in message and message["data"]:
                            print(f"[TTS DEBUG] Got audio data chunk, length: {len(message['data'])}")
                            audio_chunk = base64.b64decode(message["data"])
                            if audio_chunk:
                                print(f"[TTS DEBUG] Yielding audio chunk, decoded size: {len(audio_chunk)} bytes")
                                yield TTSChunkEvent.create(audio_chunk)
                        else:
                            print(f"[TTS DEBUG] Message has no audio data: {message}")

                        if message.get("done"):
                            print("[TTS DEBUG] Audio generation complete (done=true)")
                            break

                        if message.get("error"):
                            print(f"[TTS DEBUG] Cartesia API error: {message['error']}")
                            break

                    except json.JSONDecodeError as e:
                        print(f"[TTS DEBUG] JSON decode error: {e}, raw message: {raw_message[:200]}")
                        continue

            except websockets.exceptions.ConnectionClosed as e:
                print(f"[TTS DEBUG] Cartesia WebSocket closed: {e}")

            finally:
                print("[TTS DEBUG] Cleaning up Cartesia connection")
                if self._ws and self._ws.close_code is None:
                    try:
                        await self._ws.close()
                    except Exception as e:
                        print(f"[TTS DEBUG] Error closing WebSocket: {e}")
                self._ws = None

    async def close(self) -> None:
        if self._ws and self._ws.close_code is None:
            await self._ws.close()
        self._ws = None
        self._close_signal.set()

    async def _ensure_connection(self) -> WebSocketClientProtocol:
        if self._close_signal.is_set():
            raise RuntimeError("CartesiaTTS tried establishing a connection after it was closed")

        if self._ws and self._ws.close_code is None:
            print("[TTS DEBUG] Reusing existing WebSocket connection")
            return self._ws

        print("[TTS DEBUG] Establishing new Cartesia connection...")
        url = (
            f"wss://api.cartesia.ai/tts/websocket"
            f"?api_key={self.api_key}&cartesia_version={self.cartesia_version}"
        )

        try:
            self._ws = await websockets.connect(url)
            print("[TTS DEBUG] Cartesia WebSocket connected successfully")
            self._connection_signal.set()
            return self._ws
        except Exception as e:
            print(f"[TTS DEBUG] Failed to connect to Cartesia: {e}")
            raise
