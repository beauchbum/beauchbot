"""
System tools for BeauchBot.

Provides basic system functionality like getting current time.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from agents import function_tool


@function_tool
def get_current_time() -> str:
    """Get the current date and time in Eastern Time (EST/EDT).
    
    Returns the current date and time in Eastern timezone as an ISO 8601 formatted string 
    (e.g., '2024-03-15T14:30:00-05:00'). Automatically handles EST/EDT transitions.
    Useful for timestamping, scheduling, or time-based calculations.
    
    Returns:
        Current Eastern Time as ISO 8601 formatted string
    """
    # Get current time in Eastern timezone (handles EST/EDT automatically)
    eastern_time = datetime.now(ZoneInfo("America/New_York"))
    return eastern_time.isoformat()