import os
from fastmcp import FastMCP

# Create the main MCP server instance
beauchbot_mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "beauchbot-server"),
) 