 # async def receive_events(self)->AsyncIterator[TTSChunkEvent]:
  #   """Receive audio chunks from Cartesia WebSocket"""
  #   print("[CARTESIA] Startign receive_events loop")
  #   while not self._close_signal.is_set():
      
      
  #     _, pending = await asyncio.wait(
  #       [
  #         asyncio.create_task(self._close_signal.wait()),
  #         asyncio.create_task(self._connection_signal.wait()),
  #       ],
  #       return_when=asyncio.FIRST_COMPLETED,
  #     )
  #     with contextlib.suppress(asyncio.CancelledError):
  #       for task in pending:
  #         task.cancel()
  #     if self._close_signal.is_set():
  #       break 

  #     if self._ws and self._ws.close_code is None:
  #       self._connection_signal.clear()
  #       try:
  #         async for raw_message in self._ws:
  #           try:
  #             message = json.loads(raw_message)
  #             if "data" in message and message["data"] is not None:
  #               audio_chunk = base64.b64decode(message["data"])
  #               if audio_chunk:
  #                 yield TTSChunkEvent.create(audio_chunk)
  #             if message.get("done"):
  #               break 
  #             if "error" in message and message["error"]:
  #               print(f"[DEBUG] Cartesia error: {message['error']}")
  #               break 
  #           except json.JSONDecodeError as e:
  #             print(f"[DEBUG] Cartesia JSON decode error: {e}")
  #             continue 
  #       except websockets.exceptions.ConnectionClosed:
  #         print("Catesia: WebSocket connection closed")
  #       finally:
  #         if self._ws and self._ws.close_code is None:
  #           await self._ws.close()
  #         self._ws = None 




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
#     print(f"[CARTESIA] Sending text: '{text[:50]}'...")
#     await ws.send(json.dumps(payload))
#     print(f"[CARTESIA] Text sent successfully")

 
#   async def receive_events(self) -> AsyncIterator[TTSChunkEvent]:
#     """Receive audio chunks from Cartesia WebSocket"""
#     print("[CARTESIA] starting receive_events loop")

#     while not self._connection_signal.is_set():
#       # wait for connection to be established
#       await self._connection_signal.wait()
#       if self._ws and self._ws.close_code is None:
#         self._connection_signal.clear()
#         print("[CARTESIA] ready to receive audio")

#         try:
#           async for raw_message in self._ws:
#             try:
#               message = json.loads(raw_message)
#               msg_type = message.get("type","unknown")
#               print(f"[CARTESIA] received message type: {msg_type}")

#               # handle audio data

#               if "data" in message and message["data"] is not None:
#                 audio_chunk = base64.b64decode(message["data"])
#                 if audio_chunk:
#                   print(f"[CARTESIA] Audio chunk: {len(audio_chunk)} bytes")
#                   yield TTSChunkEvent.create(audio_chunk)

#               # handle completion

#               if message.get("done"):
#                 print("[CARTESIA] Stream done")

#               # handle errors 
#               if "error" in message and message["error"]:
#                 print(f"[CARTESIA] Error {message['error']}")

#             except json.JSONDecodeError as e:
#               print(f"[CARTESIA] JSON decode error : {e}, raw:{raw_message[:100]}")
#               continue
#         except websockets.exceptions.ConnectionClosed as e:
#           print(f"[CARTESIA] WebSocket closed : {e}")
#           self._ws = None
#         except Exception as e:
#           print(f"[CARTESIA] Unexpected error: {e}")
#           import traceback
#           traceback.print_exv()
#           self._ws = None 

#       else:

#         # wait a bit before checking again
#         await asyncio.sleep(0.1)
#     print("[CARTESIA] receive_events loop ended")




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
    _connection_signal: asyncio.Event
    _close_signal: asyncio.Event 

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: str = "f6ff7c0c-e396-40a9-a70b-f7607edb6937",
        model_id: str = "sonic-3",
        sample_rate: int = 24000,
        encoding: Literal["pcm_s16le", "pcm_f32le", "pcm_mulaw", "pcm_alaw"] = "pcm_s16le",
        language: str = "en",
        cartesia_version: str = "2024-06-10",
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
        if text is None:
            return 
        if not text.strip():
            return 
        
        ws = await self._ensure_connection()

        payload = {
            "model_id": self.model_id,
            "transcript": text,
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
            "context_id": self._generate_context_id(),
        }
        
        print(f"[CARTESIA] Sending text: '{text[:50]}'...")
        await ws.send(json.dumps(payload))
        print(f"[CARTESIA] Text sent successfully")

    async def receive_events(self) -> AsyncIterator[TTSChunkEvent]:
        """Receive audio chunks from Cartesia WebSocket."""
        print("[CARTESIA] Starting receive_events loop")
        
        while not self._close_signal.is_set():  # FIXED: was _connection_signal
            # Wait for connection to be established
            await self._connection_signal.wait()
            
            if self._ws and self._ws.close_code is None:
                self._connection_signal.clear()
                print("[CARTESIA] Ready to receive audio")
                
                try:
                    async for raw_message in self._ws:
                        try:
                            message = json.loads(raw_message)
                            msg_type = message.get("type", "unknown")
                            print(f"[CARTESIA] Received message type: {msg_type}")
                            
                            # Handle audio data
                            if "data" in message and message["data"] is not None:
                                audio_chunk = base64.b64decode(message["data"])
                                if audio_chunk:
                                    print(f"[CARTESIA] Audio chunk: {len(audio_chunk)} bytes")
                                    yield TTSChunkEvent.create(audio_chunk)
                            
                            # Handle completion
                            if message.get("done"):
                                print("[CARTESIA] Stream done")
                            
                            # Handle errors
                            if "error" in message and message["error"]:
                                print(f"[CARTESIA] Error: {message['error']}")
                                
                        except json.JSONDecodeError as e:
                            print(f"[CARTESIA] JSON decode error: {e}")
                            continue
                            
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"[CARTESIA] WebSocket closed: {e}")
                    self._ws = None
                except Exception as e:
                    print(f"[CARTESIA] Unexpected error: {e}")
                    import traceback
                    traceback.print_exc()  # FIXED: was print_exv()
                    self._ws = None
            else:
                # Wait a bit before checking again
                await asyncio.sleep(0.1)
        
        print("[CARTESIA] receive_events loop ended")

    async def close(self) -> None:
        if self._ws and self._ws.close_code is None:
            await self._ws.close()
        self._ws = None
        self._close_signal.set()

    async def _ensure_connection(self) -> WebSocketClientProtocol:
        if self._close_signal.is_set():
            raise RuntimeError(
                "CartesiaTTS tried establishing a connection after it was closed"
            )
        if self._ws and self._ws.close_code is None:
            return self._ws
        
        url = (
            f"wss://api.cartesia.ai/tts/websocket"
            f"?api_key={self.api_key}&cartesia_version={self.cartesia_version}"
        )
        
        print(f"[CARTESIA] Connecting to WebSocket...")
        self._ws = await websockets.connect(url)
        self._connection_signal.set()
        print(f"[CARTESIA] WebSocket connected")
        return self._ws