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
    python scripts/ping_agent.py              # Execute cron job
    python scripts/ping_agent.py --dry-run    # Test without execution
    python scripts/ping_agent.py --verbose    # Enable debug logging

Typical cron entry (runs every hour):
    0 * * * * cd /path/to/beauchbot && python scripts/ping_agent.py >> /var/log/beauchbot_cron.log 2>&1
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory import get_cron_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_cron_execution() -> int:
    """
    Execute the cron job by instantiating the agent and running its instructions.
    
    Args:
        dry_run: If True, initialize agent but don't execute instructions
        
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
        agent = get_cron_agent()
        logger.info("✅ Agent initialized successfully")
        
        # Execute the agent with a standard cron context
        cron_context = f"""
It is now {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    exit_code = run_cron_execution()
    
    if exit_code == 0:
        logger.info("🎉 Cron job completed successfully")
    else:
        logger.error("💥 Cron job failed")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())