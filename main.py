from typing import Optional
import os
import logging

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from pydantic import BaseModel
from smolagents import LiteLLMModel, ToolCallingAgent, ToolCollection

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/agent")
async def agent(query: str):
    model = LiteLLMModel(model_id="openai/gpt-4o-mini", temperature=0.0, api_key=os.environ["OPENAI_API_KEY"])

    with ToolCollection.from_mcp({"url": "http://mcp:8888/mcp", "transport": "streamable-http"}, trust_remote_code=True) as tool_collection:
        agent = ToolCallingAgent(
            model=model,
            tools=[*tool_collection.tools],
            add_base_tools=True
        )
        return agent.run(query)

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
        
        # Create context for the agent about the incoming message
        message_context = f"""
You have received a text message:
- From: {From}
- To: {To}
- Message: {Body}
- Message ID: {MessageSid}

You are BeauchBot, a helpful AI assistant that can:
- Send text messages to people using the send_text tool
- Look up contacts by name using get_contact tool
- Read calendar information using read_calendar tool
- Get current time using get_current_time tool
- Access other system tools as needed

Based on this incoming message, decide what action to take. You can:
1. Send a reply back to the sender using their phone number
2. Send messages to other people if the request involves them
3. Check your calendar or perform other tasks as requested
4. Simply acknowledge the message if no specific action is needed

Be helpful, friendly, and concise in your responses. If you're unsure about something, ask for clarification.
"""

        # Instantiate the AI agent with MCP tools
        model = LiteLLMModel(
            model_id="openai/gpt-4o-mini", 
            temperature=0.1, 
            api_key=os.environ["OPENAI_API_KEY"]
        )

        with ToolCollection.from_mcp(
            {"url": "http://mcp:8888/mcp", "transport": "streamable-http"}, 
            trust_remote_code=True
        ) as tool_collection:
            agent = ToolCallingAgent(
                model=model,
                tools=[*tool_collection.tools],
                add_base_tools=True
            )
            
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
