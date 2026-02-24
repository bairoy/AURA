from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from src.prompts.agent_prompt import agent_system_prompt
from src.tools.basic_tools import get_current_time, open_url
from langchain_mcp_adapters.client import MultiServerMCPClient

_agent_with_checkpointer = None
_checkpointer = None


@wrap_tool_call
async def handle_tool_errors(request, handler):
    """Catch any tool execution error and return it as a ToolMessage
    so the graph state is never left with a dangling tool call."""
    try:
        return await handler(request)
    except Exception as e:
        print(f"🔧 Tool error caught by middleware: {e}")
        return ToolMessage(
            content=f"Tool failed: {str(e)}. Please inform the user and try a different approach.",
            tool_call_id=request.tool_call["id"],
        )


async def get_agent_with_checkpointer():
    global _agent_with_checkpointer, _checkpointer

    if _checkpointer is None:
        from src.core.config import init_checkpointer
        _checkpointer = await init_checkpointer()
        print("✅ Checkpointer initialized")

    if _agent_with_checkpointer is None:
        tools = [get_current_time, open_url]

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
            tools=tools,
            system_prompt=agent_system_prompt,
            checkpointer=_checkpointer,
            # ✅ The correct way — middleware with wrap_tool_call
            middleware=[handle_tool_errors],
        )
        print(f"✅ Agent created with {len(tools)} total tool(s)")

    return _agent_with_checkpointer