"""
System tools for BeauchBot.

Provides basic system functionality like getting current time.
"""

from datetime import datetime
from smolagents import Tool


class GetCurrentTimeTool(Tool):
    name = "get_current_time"
    description = """Get the current date and time in ISO format.
    
    Returns the current date and time as an ISO 8601 formatted string (e.g., '2024-03-15T14:30:00.123456').
    Useful for timestamping, scheduling, or time-based calculations."""
    inputs = {}
    output_type = "string"

    def forward(self) -> str:
        return datetime.now().isoformat()