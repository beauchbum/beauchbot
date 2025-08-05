"""
Agent Factory for BeauchBot

Centralizes agent creation logic for consistent agent instantiation
across different entry points (web server, scripts, tests, etc.)
"""

import os
import logging
from typing import Optional

from smolagents import LiteLLMModel, ToolCallingAgent
from google_utils import get_system_prompt_from_google_doc

# Import local tools
from tools import (
    list_google_documents,
    read_google_document, 
    send_text,
    get_conversation_history,
    get_phone_numbers,
    get_current_time
)

logger = logging.getLogger(__name__)


def create_beauchbot_agent(
    system_prompt: Optional[str] = None,
    model_id: Optional[str] = None,
    temperature: float = 0.1,
    add_base_tools: bool = True
) -> ToolCallingAgent:
    """
    Create a BeauchBot agent with the standard tool configuration.
    
    Args:
        system_prompt: Custom system prompt. If None, uses default.
        model_id: Model ID to use. If None, uses MODEL_ID env var or default.
        temperature: Model temperature (0.0-1.0)
        add_base_tools: Whether to add SmolAgents base tools
        
    Returns:
        Configured ToolCallingAgent instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        # Default system prompt
        if system_prompt is None:
            system_prompt = (
                "You are BeauchBot, a helpful AI assistant that can answer questions and help with tasks. "
                "You have access to tools for Google Docs, SMS/MMS messaging, and system utilities. "
                "Use the tools provided to you to help the user effectively."
            )
        
        # Model configuration
        if model_id is None:
            model_id = os.getenv("MODEL_ID", "openai/gpt-4o-mini")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create model
        model = LiteLLMModel(
            model_id=model_id,
            temperature=temperature,
            api_key=api_key
        )
        
        # Standard BeauchBot tools
        beauchbot_tools = [
            list_google_documents,
            read_google_document, 
            send_text,
            get_conversation_history,
            get_phone_numbers,
            get_current_time
        ]
        
        # Create agent
        agent = ToolCallingAgent(
            model=model,
            tools=beauchbot_tools,
            add_base_tools=add_base_tools,
            instructions=system_prompt
        )
        
        logger.info(f"Created BeauchBot agent with model: {model_id}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create BeauchBot agent: {e}")
        raise


def create_webhook_agent() -> ToolCallingAgent:
    """
    Create a BeauchBot agent specifically configured for webhook processing.
    
    Returns:
        ToolCallingAgent configured for webhook use
    """
    webhook_prompt = (
        "You are BeauchBot, an AI assistant that processes incoming text messages via webhooks. "
        "When you receive a message, you should:\n"
        "1. Understand what the user is asking for\n"
        "2. Use available tools to help them (Google Docs, messaging, contacts, etc.)\n"
        "3. Send appropriate responses using the send_text tool\n"
        "4. Be helpful, concise, and friendly in your responses\n\n"
        "Available tools allow you to read documents, send messages, get contact info, and more."
    )
    
    return create_beauchbot_agent(
        system_prompt=webhook_prompt,
        model_id="openai/gpt-4o-mini",  # Fast model for webhook processing
        temperature=0.1,
        add_base_tools=True
    )


def create_interactive_agent() -> ToolCallingAgent:
    """
    Create a BeauchBot agent specifically configured for interactive use.
    
    Returns:
        ToolCallingAgent configured for interactive/API use
    """
    interactive_prompt = (
        "You are BeauchBot, a helpful AI assistant. You can help users with:\n"
        "- Reading and searching Google Documents\n"
        "- Sending SMS and group messages via Twilio\n"
        "- Getting contact information\n"
        "- General questions and tasks\n\n"
        "Be thorough in your responses and explain what tools you're using when appropriate."
    )
    
    return create_beauchbot_agent(
        system_prompt=interactive_prompt,
        model_id=os.getenv("MODEL_ID", "openai/gpt-4o"),  # More capable model for interactive use
        temperature=0.0,  # More deterministic for API use
        add_base_tools=True
    )


def create_cron_agent() -> ToolCallingAgent:
    """
    Create a BeauchBot agent specifically configured for cron job execution.
    
    This agent reads its system prompt from a Google Doc specified by the
    SYSTEM_PROMPT_DOC_ID environment variable.
    
    Returns:
        ToolCallingAgent configured with Google Doc system prompt
        
    Raises:
        ValueError: If system prompt cannot be loaded from Google Doc
    """
    try:
        # Fetch system prompt from Google Doc
        system_prompt = get_system_prompt_from_google_doc()
        
        return create_beauchbot_agent(
            system_prompt=system_prompt,
            model_id=os.getenv("MODEL_ID", "openai/gpt-4o-mini"),
            temperature=0.1,
            add_base_tools=True
        )
        
    except Exception as e:
        logger.error(f"Failed to create cron agent: {e}")
        raise


# Convenience functions for specific use cases
def get_webhook_agent() -> ToolCallingAgent:
    """Get a cached webhook agent (future: implement caching if needed)."""
    return create_webhook_agent()


def get_interactive_agent() -> ToolCallingAgent:
    """Get a cached interactive agent (future: implement caching if needed)."""
    return create_interactive_agent()


def get_cron_agent() -> ToolCallingAgent:
    """Get a cached cron agent (future: implement caching if needed)."""
    return create_cron_agent()