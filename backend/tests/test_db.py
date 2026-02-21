import asyncio
from src.core.config import init_checkpointer

async def test():
  checkpointer = await init_checkpointer()
  print("Success! Checkpointer created:", checkpointer)

asyncio.run(test())