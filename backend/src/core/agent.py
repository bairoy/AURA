
from langchain.agents import create_agent
from src.prompts.agent_prompt import agent_system_prompt
from src.tools.basic_tools import get_current_time,open_url
from langchain_mcp_adapters.client import MultiServerMCPClient


# Store agent and checkpointer globally
_agent_with_checkpointer = None
_checkpointer = None


async def get_agent_with_checkpointer():
    """Get agent with initialized checkpointer and tools."""
    global _agent_with_checkpointer, _checkpointer
    
    # Initialize checkpointer once
    if _checkpointer is None:
        from src.core.config import init_checkpointer
        _checkpointer = await init_checkpointer()
        print("✅ Checkpointer initialized")
    
    # Create agent with checkpointer and tools once
    if _agent_with_checkpointer is None:
        # Basic tools
        tools = [
            get_current_time,
            open_url
            
        ]
        
        # Add MCP tools
        mcp_client = MultiServerMCPClient({
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/baijuyadav/Desktop"],
            }
        })
        
        mcp_tools = await mcp_client.get_tools()
        tools.extend(mcp_tools)
        print(f"✅ Loaded {len(mcp_tools)} MCP tools")
        
        _agent_with_checkpointer = create_agent(
            model="gpt-4o-mini",
            system_prompt=agent_system_prompt,
            checkpointer=_checkpointer,
            tools=tools,
        )
        print(f"✅ Agent created with {len(tools)} total tool(s)")
    
    return _agent_with_checkpointer