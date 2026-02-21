import asyncio
from src.core.agent import get_agent_with_checkpointer

async def test():
    print("Testing agent creation...")
    try:
        agent = await get_agent_with_checkpointer()
        print(f"✅ Agent created: {agent}")
        print(f"Agent type: {type(agent)}")
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())