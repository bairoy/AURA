import asyncio 
import websockets 

async def test():
  async with websockets.connect("ws://localhost:8000/ws") as ws:
    print("connected to backend")
    await asyncio.sleep(5)


asyncio.run(test())