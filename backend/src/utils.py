import asyncio 
from typing import Any, AsyncIterator, TypeVar 
import contextlib
T = TypeVar("T")

async def merge_async_iters(*aiters: AsyncIterator[T])-> AsyncIterator[T]:
  queue: asyncio.Queue[Any]=asyncio.Queue()
  sentinel = object()

  async def producer(aiter:AsyncIterator[T])->None:
    async for item in aiter:
      await queue.put(item)
    await queue.put(sentinel)
  tasks = [asyncio.create_task(producer(a)) for a in aiters]
  finished = 0
  try:
    while finished<len(aiters):
      item = await queue.get()
      if item is sentinel:
        finished+=1
      else:
        yield item 
  finally:
    for t in tasks:
      t.cancel()
    with contextlib.suppress(Exception):
      await asyncio.gather(*tasks,return_exceptions=True)

    