from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from src.prompts.agent_prompt import agent_system_prompt



agent = create_agent(
  model="gpt-5-nano",
  system_prompt=agent_system_prompt,
  checkpointer=InMemorySaver(),
)
