import os
import logging
from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import Response, RedirectResponse
from twilio.request_validator import RequestValidator

# Import agent factory and conversation history tool for webhook
from utils.agent_factory import create_beauchbot_agent
from utils.google_utils import get_system_prompt_from_google_doc
from tools import (
    list_google_documents,
    read_google_document, 
    get_conversation_history,
    text_me,
    get_phone_numbers,
    get_current_time
)

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_twilio_signature(request: Request):
    """
    Validate that the incoming request is from Twilio by verifying the signature.
    
    During development, you can bypass validation by setting TWILIO_WEBHOOK_DEBUG=true
    
    Raises:
        HTTPException: If signature validation fails or auth token is missing
    """
    try:
        # Check if we're in debug mode (for development/testing)
        debug_mode = os.getenv('TWILIO_WEBHOOK_DEBUG', '').lower() == 'true'
        if debug_mode:
            logger.warning("Twilio webhook signature validation is DISABLED (debug mode)")
            return None, None, None
        
        # Get auth token from environment
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if not auth_token:
            logger.error("TWILIO_AUTH_TOKEN environment variable not set")
            raise HTTPException(status_code=500, detail="Server configuration error")
        
        # Get the signature from headers
        twilio_signature = request.headers.get('X-Twilio-Signature')
        if not twilio_signature:
            logger.warning("Missing X-Twilio-Signature header")
            raise HTTPException(status_code=403, detail="Missing Twilio signature")
        
        # Create validator and validate the request
        validator = RequestValidator(auth_token)
        
        # Get the full URL (FastAPI provides this)
        request_url = str(request.url)
        
        # The form data will be available after the endpoint processes it
        # For now, we'll return the validator for use in the endpoint
        return validator, request_url, twilio_signature
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during signature validation setup: {e}")
        raise HTTPException(status_code=500, detail="Signature validation error")


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/message")
async def message_webhook(
    request: Request,
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    validation_data: tuple = Depends(validate_twilio_signature),
):
    """
    Webhook endpoint for incoming Twilio messages.
    
    This endpoint receives incoming text messages from Twilio, processes them
    through an AI agent with access to BeauchBot tools, and can respond intelligently.
    """
    try:
        # Validate Twilio signature (unless in debug mode)
        validator, request_url, twilio_signature = validation_data
        
        if validator is not None:  # Not in debug mode
            # Get form data for signature validation
            form_data = await request.form()
            form_dict = dict(form_data)
            
            # Validate the signature
            if not validator.validate(request_url, form_dict, twilio_signature):
                logger.warning(f"Invalid Twilio signature for request from {From}")
                raise HTTPException(status_code=403, detail="Invalid signature")
            
            logger.info(f"✅ Validated Twilio signature for message from {From} to {To}: {Body[:100]}...")
        else:
            logger.info(f"⚠️  Processing message from {From} to {To} (debug mode - signature not validated): {Body[:100]}...")
        
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
- Message ID: {MessageSid}
- Conversation history: {conversation_context}

Based on this incoming message, decide what action to take. You can:
1. Use the get_phone_numbers tool to get the phone numbers of the people involved
2. Read Google docs if there's missing context
3. Text your admin back if you need to using the text_me tool
4. Simply acknowledge the message if no specific action is needed

Please process this message according to your instructions.
"""

        # Standard BeauchBot tools
        tools = [
            list_google_documents,
            read_google_document, 
            get_conversation_history,
            text_me,
            get_phone_numbers,
            get_current_time
        ]

        # Instantiate the AI agent using factory
        agent = create_beauchbot_agent(
            system_prompt=get_system_prompt_from_google_doc(),
            add_base_tools=True,
            tools=tools
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
