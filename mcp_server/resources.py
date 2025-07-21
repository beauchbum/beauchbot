"""
Resources for the beauchbot MCP server.

Resources provide read-only data that can be accessed by MCP clients.
"""

from datetime import datetime
from typing import Dict, Any, List

from mcp_server.server import beauchbot_mcp


# Contacts data - can be expanded later
CONTACTS = [
    {
        "name": "Ryan",
        "phone": "+12035839125",
        "notes": "Owner/Primary contact"
    }
]


@beauchbot_mcp.resource("beauchbot://contacts")
def get_all_contacts() -> Dict[str, Any]:
    """Get all available contacts with their phone numbers."""
    return {
        "contacts": CONTACTS,
        "count": len(CONTACTS)
    }


@beauchbot_mcp.resource("beauchbot://tools")
def get_available_tools() -> Dict[str, Any]:
    """Get a list of all available tools and their descriptions."""
    tools = {}
    for tool_name, tool_obj in beauchbot_mcp._tool_manager.get_tools().items():
        tools[tool_name] = {
            "name": tool_obj.name,
            "description": tool_obj.description,
        }
    
    return {
        "tools": tools,
        "count": len(tools)
    } 