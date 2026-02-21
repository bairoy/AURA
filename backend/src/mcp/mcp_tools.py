from typing import List
from langchain_core.tools import BaseTool
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import tool as langchain_tool


async def connect_mcp_server(server_name: str, command: str, args: List[str]):
    """Connect to an MCP server and return the session."""
    print(f"🔌 Connecting to MCP server: {server_name}")
    
    server_params = StdioServerParameters(command=command, args=args)
    stdio_transport = await stdio_client(server_params)
    stdio, write = stdio_transport
    
    session = ClientSession(stdio, write)
    await session.initialize()
    
    print(f"✅ Connected to {server_name}")
    return session


async def get_mcp_tools(server_name: str, command: str, args: List[str]) -> List[BaseTool]:
    """Get tools from an MCP server and convert them to LangChain tools.
    
    Args:
        server_name: Name of the MCP server
        command: Command to start the server
        args: Arguments for the command
    
    Returns:
        List of LangChain tools
    """
    session = await connect_mcp_server(server_name, command, args)
    
    # Get available tools from MCP server
    tools_response = await session.list_tools()
    
    langchain_tools = []
    
    for mcp_tool in tools_response.tools:
        # Create a LangChain tool for each MCP tool
        @langchain_tool(name=mcp_tool.name, description=mcp_tool.description or "")
        async def mcp_tool_wrapper(tool_input: str, tool_name=mcp_tool.name, mcp_session=session):
            """Wrapper to call MCP tool."""
            result = await mcp_session.call_tool(tool_name, arguments={"input": tool_input})
            return str(result.content)
        
        langchain_tools.append(mcp_tool_wrapper)
    
    print(f"✅ Loaded {len(langchain_tools)} tools from {server_name}")
    return langchain_tools