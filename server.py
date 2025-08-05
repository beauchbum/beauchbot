from typing import Optional
import os
import logging

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from pydantic import BaseModel

# Import agent factory and conversation history tool for webhook
from agent_factory import get_interactive_agent, get_webhook_agent
from tools import get_conversation_history

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/agent")
async def agent(query: str):
    try:
        # Create agent using factory
        agent = get_interactive_agent()
        return agent.run(query)
            
    except ValueError as e:
        logger.error(f"Agent configuration error: {e}")
        return {"error": f"Agent configuration error: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error in agent endpoint: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.post("/message")
async def message_webhook(
    request: Request,
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0"),
    # Additional optional Twilio fields
    FromCity: Optional[str] = Form(default=None),
    FromState: Optional[str] = Form(default=None),
    FromCountry: Optional[str] = Form(default=None),
    AccountSid: Optional[str] = Form(default=None),
):
    """
    Webhook endpoint for incoming Twilio messages.
    
    This endpoint receives incoming text messages from Twilio, processes them
    through an AI agent with access to MCP tools, and can respond intelligently.
    """
    try:
        logger.info(f"Received message from {From} to {To}: {Body[:100]}...")
        
        # Basic validation
        if not Body.strip():
            logger.warning("Received empty message body")
            return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", 
                          media_type="application/xml")
        

        
        # Get conversation history for context
        try:
            conversation_history = get_conversation_history(From, 10)  # Get last 10 messages
            if isinstance(conversation_history, list) and len(conversation_history) > 0 and "error" not in conversation_history[0]:
                history_text = "\n".join([
                    f"[{msg['date_created'][:16]}] {'You' if msg['direction'] == 'outbound-api' else 'Them'}: {msg['body']}"
                    for msg in conversation_history[-5:]  # Show last 5 for context
                ])
                conversation_context = f"\nRecent conversation history:\n{history_text}\n"
            else:
                conversation_context = ""
        except Exception as e:
            logger.warning(f"Could not get conversation history: {e}")
            conversation_context = ""

        # Create context for the agent about the incoming message
        message_context = f"""
You have received a text message:
- From: {From}
- To: {To}
- Message: {Body}
- Message ID: {MessageSid}{conversation_context}

Based on this incoming message, decide what action to take. You can:
1. Send a reply back to the sender using their phone number
2. Send messages to other people if the request involves them
4. Simply acknowledge the message if no specific action is needed

Please process this message according to your instructions.
"""

        # Instantiate the AI agent using factory
        agent = get_webhook_agent()
        
        # Process the message through the agent
        logger.info("Processing message through AI agent...")
        agent_response = agent.run(message_context)
        
        logger.info(f"Agent processing completed. Response: {str(agent_response)[:200]}...")
        
        # Return empty TwiML response (agent will send replies via tools if needed)
        # This tells Twilio the webhook was processed successfully
        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", 
            media_type="application/xml"
        )
            
    except Exception as e:
        logger.error(f"Error processing message webhook: {e}", exc_info=True)
        
        # Return empty TwiML response even on error to avoid Twilio retries
        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", 
            media_type="application/xml"
        )
