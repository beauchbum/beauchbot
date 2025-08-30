"""
Agent Factory for BeauchBot

Centralizes agent creation logic for consistent agent instantiation
across different entry points (web server, scripts, tests, etc.)
"""

import os
import logging
from typing import List, Callable

from agents import Agent

logger = logging.getLogger(__name__)

def create_beauchbot_agent(
    system_prompt: str,
    tools: List[Callable],
    add_base_tools: bool = False
) -> Agent:
    """
    Create a BeauchBot agent with the standard tool configuration.
    
    Args:
        system_prompt: Custom system prompt/instructions for the agent
        tools: List of function tools to provide to the agent
        add_base_tools: Whether to add base tools (unused in openai-agents, kept for compatibility)
        
    Returns:
        Configured Agent instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        # Validate required environment variables
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create agent with OpenAI Agents framework
        agent = Agent(
            name="BeauchBot",
            instructions=system_prompt,
            model="gpt-4o",  # Use GPT-4o as default model
            tools=tools
        )
        
        logger.info("✅ BeauchBot agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create BeauchBot agent: {e}")
        raise


def create_webhook_agent() -> Agent:
    """
    Create a BeauchBot agent specifically configured for webhook processing.
    
    Returns:
        Agent configured for webhook use
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
    
    # Import tools here to avoid circular imports
    from tools import (
        list_google_documents,
        read_google_document, 
        get_conversation_history,
        text_me,
        get_phone_numbers,
        get_current_time,
        send_text
    )
    
    tools = [
        list_google_documents,
        read_google_document, 
        get_conversation_history,
        text_me,
        get_phone_numbers,
        get_current_time,
        send_text
    ]
    
    return create_beauchbot_agent(
        system_prompt=webhook_prompt,
        tools=tools,
        add_base_tools=True
    )


def create_interactive_agent() -> Agent:
    """
    Create a BeauchBot agent specifically configured for interactive use.
    
    Returns:
        Agent configured for interactive/API use
    """
    interactive_prompt = (
        "You are BeauchBot, a helpful AI assistant. You can help users with:\n"
        "- Reading and searching Google Documents\n"
        "- Sending SMS and group messages via Twilio\n"
        "- Getting contact information\n"
        "- General questions and tasks\n\n"
        "Be thorough in your responses and explain what tools you're using when appropriate."
    )
    
    # Import tools here to avoid circular imports
    from tools import (
        list_google_documents,
        read_google_document, 
        get_conversation_history,
        text_me,
        get_phone_numbers,
        get_current_time,
        send_text
    )
    
    tools = [
        list_google_documents,
        read_google_document, 
        get_conversation_history,
        text_me,
        get_phone_numbers,
        get_current_time,
        send_text
    ]
    
    return create_beauchbot_agent(
        system_prompt=interactive_prompt,
        tools=tools,
        add_base_tools=True
    )


# Convenience functions for specific use cases
def get_webhook_agent() -> Agent:
    """Get a cached webhook agent (future: implement caching if needed)."""
    return create_webhook_agent()


def get_interactive_agent() -> Agent:
    """Get a cached interactive agent (future: implement caching if needed)."""
    return create_interactive_agent()
