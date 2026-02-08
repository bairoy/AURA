from typing import AsyncIterator 
from src.events import VoiceAgentEvent
from src.cartesia_tts import CartesiaTTS
from src.utils import merge_async_iters

async def tts_stream(
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
