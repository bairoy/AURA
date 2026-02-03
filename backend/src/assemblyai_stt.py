# import asyncio 
# import contextlib 
# import json 
# import os 
# from typing import AsyncIterator, Optional 
# from urllib.parse import urlencode 
# import base64

# import websockets 
# from websockets.client import WebSocketClientProtocol

# from src.events import STTChunkEvent,STTEvent,STTOutputEvent

# class AssemblyAISTT:
#   def __init__(
#       self,
#       api_key:Optional[str]=None,
#       sample_rate:int = 16000,
#       format_turns:bool = True,
#   ):
#     self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
#     if not self.api_key:
#       raise ValueError("AssemblyAI API key is required")
    
#     self.sample_rate = sample_rate
#     self.format_turns = format_turns
#     self._ws: Optional[WebSocketClientProtocol]=None 
#     self._connection_signal = asyncio.Event()
#     self._close_signal = asyncio.Event()

#   async def receive_events(self)->AsyncIterator[STTEvent]:
#     while not self._close_signal.is_set():
#       _,pending = await asyncio.wait(
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
#               message_type = message.get("type")

#               if message_type == "Begin":
#                 pass
#               elif message_type == "Turn":
#                 transcript = message.get("transcript","")
#                 turn_is_formatted = message.get(
#                   "turn_is_formatted",False
#                 )
#                 if turn_is_formatted:
#                   if transcript:
#                     yield STTOutputEvent.create(transcript)
#                 else:
#                   yield STTChunkEvent.create(transcript)

#               elif message_type == "Termination":
#                 pass 
#               else:
#                 if "error" in message:
#                   print(f"AssemblyAISTT error: {message['error']}")
#                   break
#             except json.JSONDecodeError as e:
#               print(f"[DEBUG] AssemblyAISTT JSON decode error: {e}")
#               continue 

#         except websockets.exceptions.ConnectionClosed:
#           print("AssemblyAISTT: WebSocket connection closed")

#   async def send_audio(self,audio_chunk:bytes)->None:
#     ws = await self._ensure_connection()
#     print("SENT TO ASSSEMBLY: ",len(audio_chunk))
#     payload = {
#       "audio": base64.b64encode(audio_chunk).decode("ascii")
#     }
#     await ws.send(json.dumps(payload))

#   async def close(self)->None:
#     if self._ws and self._ws.close_code is None:
#       await self._ws.close()
#       self._ws = None 
#       self._close_signal.set()

#   async def _ensure_connection(self)->WebSocketClientProtocol:
#     if self._close_signal.is_set():
#       raise RuntimeError(
#         "AssemblyAISTT tried establishing a connection after it was closed"
#       )
#     if self._ws and self._ws.close_code is None:
#       return self._ws 
    
#     params = urlencode(
#       {
#         "sample_rate":self.sample_rate,
#         "format_turns":str(self.format_turns).lower(),
#         "encoding":"opus",
#       }
#     )
#     url = f"wss://streaming.assemblyai.com/v3/ws?{params}"
#     self._ws = await websockets.connect(
#       url,additional_headers={"Authorization":self.api_key}
#     )
#     start_message = {
#       "type":"Start",
#       "sample_rate":self.sample_rate,
#       "encoding":"opus",
#     }
#     await self._ws.send(json.dumps(start_message))
#     self._connection_signal.set()
#     return self._ws 
import asyncio
import contextlib
import json
import os
import base64
from typing import AsyncIterator, Optional
from urllib.parse import urlencode

import websockets
from websockets.client import WebSocketClientProtocol

from src.events import STTChunkEvent, STTEvent, STTOutputEvent


class AssemblyAISTT:
    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = 16000,
        format_turns: bool = True,
    ):
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("AssemblyAI API key is required")

        self.sample_rate = sample_rate
        self.format_turns = format_turns

        self._ws: Optional[WebSocketClientProtocol] = None
        self._connection_signal = asyncio.Event()
        self._close_signal = asyncio.Event()

    # ----------------------------
    # Receive transcription events
    # ----------------------------

    async def receive_events(self) -> AsyncIterator[STTEvent]:

        while not self._close_signal.is_set():

            _, pending = await asyncio.wait(
                [
                    asyncio.create_task(self._close_signal.wait()),
                    asyncio.create_task(self._connection_signal.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                with contextlib.suppress(asyncio.CancelledError):
                    task.cancel()

            if self._close_signal.is_set():
                break

            if not self._ws or self._ws.close_code is not None:
                continue

            self._connection_signal.clear()

            try:
                async for raw_message in self._ws:

                    try:
                        message = json.loads(raw_message)
                        msg_type = message.get("type")

                        if msg_type == "Begin":
                            continue

                        elif msg_type == "Turn":
                            transcript = message.get("transcript", "")
                            is_formatted = message.get("turn_is_formatted", False)

                            if is_formatted:
                                if transcript:
                                    yield STTOutputEvent.create(transcript)
                            else:
                                yield STTChunkEvent.create(transcript)

                        elif msg_type == "Termination":
                            break

                        elif "error" in message:
                            print("AssemblyAI error:", message["error"])
                            break

                    except json.JSONDecodeError:
                        continue

            except websockets.exceptions.ConnectionClosed:
                print("AssemblyAISTT: WebSocket connection closed")

    # ----------------------------
    # Send raw PCM audio
    # ----------------------------

    async def send_audio(self, audio_chunk: bytes) -> None:

        ws = await self._ensure_connection()

        # payload = {
        #     "audio": base64.b64encode(audio_chunk).decode("ascii")
        # }

        # await ws.send(json.dumps(payload))
        await ws.send(audio_chunk)

    # ----------------------------
    # Close connection
    # ----------------------------

    async def close(self) -> None:

        if self._ws and self._ws.close_code is None:
            await self._ws.close()

        self._ws = None
        self._close_signal.set()

    # ----------------------------
    # Create / ensure websocket
    # ----------------------------

    async def _ensure_connection(self) -> WebSocketClientProtocol:

        if self._close_signal.is_set():
            raise RuntimeError("AssemblyAISTT used after close")

        if self._ws and self._ws.close_code is None:
            return self._ws

        # # IMPORTANT: use PCM not opus
        # params = urlencode(
        #     {
        #         "sample_rate": self.sample_rate,
        #         "format_turns": str(self.format_turns).lower(),
        #         "encoding": "pcm_s16le",
        #     }
        # )
        params = urlencode({
            "sample_rate":self.sample_rate,
            "format_turns":str(self.format_turns).lower(),
        })

        url = f"wss://streaming.assemblyai.com/v3/ws?{params}"

        self._ws = await websockets.connect(
            url,
            additional_headers={
                "Authorization": self.api_key
            },
        )

        # # Start message (must match PCM encoding)
        # start_message = {
        #     "type": "Start",
        #     "sample_rate": self.sample_rate,
        #     "encoding": "pcm_s16le",
        # }

        # await self._ws.send(json.dumps(start_message))

        self._connection_signal.set()

        return self._ws
