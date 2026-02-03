import asyncio 
import contextlib 
from pathlib import Path 
from typing import AsyncIterator
from uuid import uuid4


import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI,WebSocket 
# from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import create_agent
from langchain.messages import AIMessage,HumanMessage,ToolMessage 
from langchain_core.runnables import RunnableGenerator
from langgraph.checkpoint.memory import InMemorySaver
# from startlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.assemblyai_stt import AssemblyAISTT
from src.cartesia_tts import CartesiaTTS
from src.events import (
  AgentChunkEvent,
  AgentEndEvent,
  ToolCallEvent,
  ToolResultEvent,
  VoiceAgentEvent,
  event_to_dict,
)
from src.utils import merge_async_iters
load_dotenv()
app = FastAPI()
app.add_middleware(
   CORSMiddleware,
   allow_origins=["http://localhost:3000","http://localhost:8000"],
   allow_methods=["*"],
   allow_headers=["*"],
)


system_prompt = """You are helpful personal assistant, Your goal is to take the user message and perform action and reply"""

agent = create_agent(
  model="gpt-5-nano",
  system_prompt=system_prompt,
  checkpointer=InMemorySaver(),
)
async def _stt_stream(
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



async def _agent_stream(event_stream:AsyncIterator[VoiceAgentEvent],)->AsyncIterator[VoiceAgentEvent]:
  thread_id = str(uuid4())
  async for event in event_stream:
    yield event 
    if event.type == "stt_output":
      stream = agent.astream(
        {"messages":[HumanMessage(content=event.transcript)]},
        {"configurable":{"thread_id":thread_id}},
        stream_mode="messages",
      )   
      async for message,metadata in stream:
        if isinstance(message,AIMessage):
          yield AgentChunkEvent.create(message.content)
          if hasattr(message,"tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
              yield ToolCallEvent.create(
                id=tool_call.get("id",str(uuid4())),
                name=tool_call.get("name","unknown"),
                args = tool_call.get("args",{}),
              )  
        if isinstance(message,ToolMessage):
            yield ToolResultEvent.create(
              tool_call_id=getattr(message,"tool_call_id",""),
              name=getattr(message,"name","unknown"),
              result=str(message.content) if message.content else "",
            ) 
      yield AgentEndEvent.create()

async def _tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
)-> AsyncIterator[VoiceAgentEvent]:
  """
  args:
   event_stream: An asyncc iterator of upstream voice agent events
  yields:
  all upstream events plus tts_chunk events for synthesized audio

  """
  tts = CartesiaTTS()

  async def process_upstream()->AsyncIterator[VoiceAgentEvent]:
    buffer:list[str] = []
    async for event in event_stream:
      yield event 
      if event.type == "agent_chunk":
        buffer.append(event.text)
      if event.type == "agent_end":
        await tts.send_text("".join(buffer))
        buffer = []

  try:
    async for event in merge_async_iters(process_upstream(),tts.receive_events()):
      yield event
  finally:
    await tts.close()

pipeline = (RunnableGenerator(_stt_stream)
            | RunnableGenerator(_agent_stream)
            | RunnableGenerator(_tts_stream))
@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket):
  await websocket.accept()
  async def websocket_audio_stream()->AsyncIterator[bytes]:
    try:
      while True:
        msg = await websocket.receive()
        msg_type = msg.get("type")

        if msg_type == "websocket.receive" and "bytes" in msg:
           yield msg["bytes"]

        elif msg_type == "websocket.disconnect":
           print("WebSocket disconnected:",msg.get("code"))
           break

    except RuntimeError as e:
       print("Websocket receive stopped: ",e)
      
  output_stream = pipeline.atransform(websocket_audio_stream())
  async for event in output_stream:
    await websocket.send_json(event_to_dict(event))

root = Path(__file__).resolve().parent.parent.parent / "frontend"

app.mount("/", StaticFiles(directory=str(root), html=True), name="frontend")


if __name__ == "__main__":
  uvicorn.run("main:app",port=8000,reload=True)
  

