#!/usr/bin/env python3
"""
Ping Agent Script for BeauchBot - Cron Job Entry Point

This script is designed to be run as a cron job (e.g., hourly).
It instantiates a BeauchBot agent that reads its system prompt from a Google Doc
and executes the instructions contained within that prompt.

The system prompt document should contain instructions for what the agent
should do during its scheduled execution (e.g., check calendar, send reminders,
process pending tasks, etc.).

Environment Variables Required:
- OPENAI_API_KEY: OpenAI API key for the LLM
- GOOGLE_SERVICE_ACCOUNT_B64: Base64 encoded Google service account JSON
- SYSTEM_PROMPT_DOC_ID: Google Doc ID containing the system prompt
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER: For messaging

Usage:
    python scripts/ping_agent.py                                    # Execute cron job with current Eastern time
    python scripts/ping_agent.py --dry-run                          # Dry run (no text_me tool)
    python scripts/ping_agent.py --simulate-time "2024-01-15 09:00" # Test with simulated time (9 AM EST)
    python scripts/ping_agent.py -t "2024-12-25"                    # Test Christmas day (midnight EST)
    python scripts/ping_agent.py -t "2024-06-15 18:30:00"           # Test specific time with seconds (EST)

Typical cron entry (runs every hour):
    0 * * * * cd /path/to/beauchbot && python scripts/ping_agent.py >> /var/log/beauchbot_cron.log 2>&1
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.agent_factory import create_beauchbot_agent
from utils.google_utils import get_system_prompt_from_google_doc
from tools import (
    list_google_documents,
    read_google_document, 
    send_text,
    get_conversation_history,
    text_me,
    get_phone_numbers,
    get_current_time
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_simulated_time(simulated_time: str) -> datetime:
    """Parse the simulated time string and return a datetime object."""
    if len(simulated_time.split(",")) == 2:  # "YYYY-MM-DD HH:MM"
        naive_time = datetime.strptime(simulated_time, '%Y-%m-%d,%H:%M')
    elif len(simulated_time.split(",")) == 1:  # "YYYY-MM-DD" (assume midnight)
        naive_time = datetime.strptime(simulated_time, '%Y-%m-%d')
    return naive_time.replace(tzinfo=ZoneInfo("America/New_York"))


def run_cron_execution(simulated_time: str = None, dry_run: bool = False) -> int:
    """
    Execute the cron job by instantiating the agent and running its instructions.
    
    Args:
        simulated_time: Optional datetime string to simulate (format: "YYYY-MM-DD HH:MM")
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    start_time = datetime.now()
    logger.info(f"Starting BeauchBot cron execution at {start_time}")
    
    try:
        # Check required environment variables
        required_vars = [
            "OPENAI_API_KEY",
            "GOOGLE_SERVICE_ACCOUNT_B64", 
            "SYSTEM_PROMPT_DOC_ID"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return 1
        
        # Initialize the cron agent (this will read the system prompt from Google Doc)
        logger.info("Initializing BeauchBot cron agent...")
        system_prompt = get_system_prompt_from_google_doc()
        
        # Standard BeauchBot tools
        beauchbot_tools = [
            list_google_documents,
            read_google_document, 
            send_text,
            get_conversation_history,
            text_me,
            get_phone_numbers
        ]
        
        agent =  create_beauchbot_agent(
            system_prompt=system_prompt,
            add_base_tools=True,
            tools=beauchbot_tools if not dry_run else [tool for tool in beauchbot_tools if tool.name not in ["send_text", "text_me"]]
        )
        logger.info("✅ Agent initialized successfully")
        
        # Get Eastern timezone for all time operations
        eastern_tz = ZoneInfo("America/New_York")
        
        # Determine the time to use (actual or simulated) - always in Eastern time
        if simulated_time:
            try:
                current_time_obj = parse_simulated_time(simulated_time)
                current_time_str = current_time_obj.strftime('%Y-%m-%d %I:%M %p')
                logger.info(f"🕐 Using simulated time: {current_time_str}")
                
            except ValueError as e:
                logger.error(f"Invalid simulated time format: {simulated_time}. Use format 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'")
                return 1
        else:
            # Use actual current time in Eastern timezone
            current_time_obj = datetime.now(eastern_tz)
            current_time_str = current_time_obj.strftime('%Y-%m-%d %I:%M %p')
        
        # Execute the agent with the cron context (using actual or simulated Eastern time)
        time_context = "simulated" if simulated_time else "actual"
        cron_context = f"""
The current time is {current_time_str} ({time_context} Eastern time).

You are running as a scheduled cron job. Execute the instructions in your system prompt.

Use your available tools as needed to complete your tasks. 
"""
        
        logger.info("🤖 Executing cron instructions...")
        response = agent.run(cron_context)
        
        # Log the response
        logger.info("✅ Cron execution completed successfully")
        logger.info(f"Agent response: {str(response)[:500]}{'...' if len(str(response)) > 500 else ''}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Cron execution finished at {end_time} (duration: {duration})")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Cron execution failed: {e}", exc_info=True)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BeauchBot cron job entry point",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Dry run the cron job (initialize agent but without tools to text)"
    )
    parser.add_argument(
        "--simulate-time", "-t",
        help="Simulate a specific time in Eastern timezone (format: 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD')"
    )
    
    args = parser.parse_args()
    
    eastern_tz = ZoneInfo("America/New_York")
    now = parse_simulated_time(args.simulate_time) if args.simulate_time else datetime.now(eastern_tz)
    if now.hour >= 9 and now.hour < 21:
        exit_code = run_cron_execution(simulated_time=args.simulate_time, dry_run=args.dry_run)
    else:
        logger.info("It's not time to run the cron job")
        exit_code = 0
    
    if exit_code == 0:
        logger.info("Cron job completed successfully")
    else:
        logger.error("Cron job failed")
    
    return exit_code


if __name__ == "__main__":
    
    sys.exit(main())