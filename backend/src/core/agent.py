import asyncio
from langchain.agents import create_agent
from src.prompts.agent_prompt import agent_system_prompt
from src.core.config import init_checkpointer


# initialize checkpointer (async → sync at import time)
checkpointer = asyncio.run(init_checkpointer())

# create global agent instance
agent = create_agent(
    model="gpt-5-nano",
    system_prompt=agent_system_prompt,
    checkpointer=None,
)
