"""
Agent Factory for BeauchBot

Centralizes agent creation logic for consistent agent instantiation
across different entry points (web server, scripts, tests, etc.)
"""

import os
import logging

from smolagents import LiteLLMModel, ToolCallingAgent, Tool, LogLevel
import litellm

litellm.turn_off_message_logging = True

logger = logging.getLogger(__name__)

def create_beauchbot_agent(
    system_prompt: str,
    model_id: str,
    temperature: float,
    tools: list[Tool],
    add_base_tools: bool
) -> ToolCallingAgent:
    """
    Create a BeauchBot agent with the standard tool configuration.
    
    Args:
        system_prompt: Custom system prompt.
        model_id: Model ID to use.
        temperature: Model temperature (0.0-1.0)
        add_base_tools: Whether to add SmolAgents base tools
        
    Returns:
        Configured ToolCallingAgent instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        # Model configuration        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create model
        model = LiteLLMModel(
            model_id=model_id,
            temperature=temperature,
            api_key=api_key
        )
        
        
        
        # Create agent
        agent = ToolCallingAgent(
            model=model,
            tools=tools,
            add_base_tools=add_base_tools,
            instructions=system_prompt,
            verbosity_level=LogLevel.ERROR
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


# Convenience functions for specific use cases
def get_webhook_agent() -> ToolCallingAgent:
    """Get a cached webhook agent (future: implement caching if needed)."""
    return create_webhook_agent()


def get_interactive_agent() -> ToolCallingAgent:
    """Get a cached interactive agent (future: implement caching if needed)."""
    return create_interactive_agent()
