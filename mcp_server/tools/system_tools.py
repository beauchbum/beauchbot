import os
import platform
from datetime import datetime
from typing import Dict, Any

from mcp_server.server import beauchbot_mcp


@beauchbot_mcp.tool()
def get_current_time() -> str:
    """Get the current date and time in ISO format."""
    return datetime.now().isoformat()
