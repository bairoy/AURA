from dotenv import load_dotenv
load_dotenv()
import asyncio 
from src.cartesia_tts import CartesiaTTS

async def test():
  tts = CartesiaTTS()

  # start receiving in background
  async def receive():
    async for event in tts.receive_events():
      print(f"Got audio: {len(event.audio)} bytes")
    
  receive_task = asyncio.create_task(receive())

  # wait a bit then send text
  await asyncio.sleep(0.5)
  await tts.send_text("Hello world")

  # wait for audio 
  await asyncio.sleep(3)

  await tts.close()
  receive_task.cancel()

asyncio.run(test())