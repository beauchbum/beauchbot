"""
Agent Factory for BeauchBot

Centralizes agent creation logic for consistent agent instantiation
across different entry points (web server, scripts, tests, etc.)
"""

import os
import logging

from smolagents import LiteLLMRouterModel, ToolCallingAgent, Tool, LogLevel
import litellm

litellm.turn_off_message_logging = True

logger = logging.getLogger(__name__)

def create_beauchbot_agent(
    system_prompt: str,
    tools: list[Tool],
    add_base_tools: bool
) -> ToolCallingAgent:
    """
    Create a BeauchBot agent with the standard tool configuration.
    
    Args:
        system_prompt: Custom system prompt.
        add_base_tools: Whether to add SmolAgents base tools
        
    Returns:
        Configured ToolCallingAgent instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        model = LiteLLMRouterModel(
            model_id="anthropic/claude-sonnet-4-20250514",
            model_list=[
                {
                    "model_name": "anthropic/claude-sonnet-4-20250514",
                    "litellm_params": {"model": "anthropic/claude-sonnet-4-20250514"},
                },
                {
                    "model_name": "openai/gpt-5",
                    "litellm_params": {"model": "openai/gpt-5"},
                },
                {
                    "model_name": "openai/gpt-4.1",
                    "litellm_params": {"model": "openai/gpt-4.1"},
                }
            ],
            num_retries=3
        )
        
        # Create agent
        agent = ToolCallingAgent(
            model=model,
            tools=tools,
            add_base_tools=add_base_tools,
            instructions=system_prompt,
            verbosity_level=LogLevel.ERROR
        )
        
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
        add_base_tools=True
    )


# Convenience functions for specific use cases
def get_webhook_agent() -> ToolCallingAgent:
    """Get a cached webhook agent (future: implement caching if needed)."""
    return create_webhook_agent()


def get_interactive_agent() -> ToolCallingAgent:
    """Get a cached interactive agent (future: implement caching if needed)."""
    return create_interactive_agent()
