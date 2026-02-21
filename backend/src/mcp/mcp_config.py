"""MCP Server configurations."""

# List of MCP servers to connect to
MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/baijuyadav/Desktop"],
        "description": "Access and manage files on the filesystem"
    },
     "airbnb": {
      "command": "npx",
      "args": [
        "-y",
        "@openbnb/mcp-server-airbnb",
        "--ignore-robots-txt"
      ]
    },
   
    # Add more servers here later
}