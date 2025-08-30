import os
import logging
from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import Response, RedirectResponse
from twilio.request_validator import RequestValidator

# Import agent factory and conversation history tool for webhook
from utils.agent_factory import create_beauchbot_agent
from utils.google_utils import get_system_prompt_from_google_doc
from utils.phone_utils import validate_phone_numbers_against_contacts
from agents import Runner
from tools import (
    list_google_documents,
    read_google_document, 
    get_conversation_history,
    text_me,
    get_phone_numbers,
    get_current_time,
    send_text,
    send_text_dry
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
):
    """
    Webhook endpoint for incoming Twilio messages.
    
    This endpoint receives incoming text messages from Twilio, validates that they
    are from authorized contacts in the phone directory, and processes them through
    an AI agent with access to BeauchBot tools.
    
    Security features:
    - Twilio signature validation (bypass with TWILIO_WEBHOOK_DEBUG=true)
    - Contact authorization validation (bypass with TWILIO_BYPASS_CONTACT_VALIDATION=true)
    - Messages from unauthorized numbers are logged but ignored
    """
    try:
        # Get all form data to extract OtherRecipients and other dynamic fields
        url = str(request.url)
        form_data = await request.form()
        form_dict = dict(form_data)
        signature = request.headers.get("X-Twilio-Signature", "")

        logger.info(url)
        logger.info(form_dict)
        logger.info(signature)

        if os.getenv('TWILIO_WEBHOOK_DEBUG', '').lower() == 'true':
            logger.warning("Twilio webhook signature validation is DISABLED (debug mode)")
        else:
            validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))
            if not validator.validate(
                url.replace("http://", "https://"), 
                form_dict, 
                signature
            ):
                raise HTTPException(status_code=400, detail="Error in Twilio Signature")
        
        # Parse OtherRecipients fields (they come as OtherParticipants[0], OtherParticipants[1], etc.)
        other_recipients = []
        for key, value in form_dict.items():
            if key.startswith('OtherRecipients['):
                other_recipients.append(value)
                logger.info(f"Found other recipient: {key} = {value}")
        
        # Log all form fields for debugging (can be removed in production)
        logger.debug(f"All webhook form fields: {list(form_dict.keys())}")
        
        # Basic validation
        if not Body.strip():
            logger.warning("Received empty message body")
            return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", 
                          media_type="application/xml")
        
        # Validate that the sender and other recipients are in our approved contacts
        # Check if contact validation is disabled for development/testing
        bypass_contact_validation = os.getenv('TWILIO_BYPASS_CONTACT_VALIDATION', '').lower() == 'true'
        
        # Collect all phone numbers to validate (sender + other recipients)
        all_phone_numbers = [From] + other_recipients
        
        if bypass_contact_validation:
            logger.warning("Contact validation is BYPASSED - accepting message from any phone number")
            matching_contacts = [{'name': 'Unknown Contact', 'phone_number': num} for num in all_phone_numbers]
            sender_contact = matching_contacts[0]
            other_contacts = matching_contacts[1:] if len(matching_contacts) > 1 else []
        else:
            valid_numbers, invalid_numbers, matching_contacts = validate_phone_numbers_against_contacts(all_phone_numbers)
            
            # Check if sender is unauthorized
            if From in invalid_numbers:
                logger.warning(f"Received message from unauthorized phone number: {From}")
                # Log the attempt but don't respond to unauthorized numbers
                return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", 
                              media_type="application/xml")
            
            # Separate sender contact from other contacts
            sender_contact = next((c for c in matching_contacts if c['phone_number'] == From), None)
            other_contacts = [c for c in matching_contacts if c['phone_number'] != From]
            
            # Log any unauthorized other recipients (but still process the message)
            if invalid_numbers:
                unauthorized_others = [num for num in invalid_numbers if num != From]
                if unauthorized_others:
                    logger.warning(f"Group message includes unauthorized recipients: {unauthorized_others}")
        
        # Log the validated contacts
        if sender_contact:
            logger.info(f"Processing message from authorized contact: {sender_contact['name']} ({From})")
        
        if other_contacts:
            other_names = [f"{c['name']} ({c['phone_number']})" for c in other_contacts]
            logger.info(f"Group message includes other authorized participants: {', '.join(other_names)}")
        

        # Create context for the agent about the incoming message
        sender_info = f" ({sender_contact['name']})" if sender_contact else ""
        
        # Build group participants information
        if other_contacts:
            group_info = "\n- Group Participants: "
            all_participants = [sender_contact['name']] if sender_contact else [From]
            all_participants.extend([c['name'] for c in other_contacts])
            group_info += ", ".join(all_participants)
            message_type = "group message"
        else:
            group_info = ""
            message_type = "individual message"

        
        
        message_context = f"""
        You have received a {message_type}:
        - From: {From}{sender_info}
        - To: {os.getenv('TWILIO_PHONE_NUMBER')}
        - Other Recipients: {', '.join(other_recipients)}
        - Message: {Body}

        Based on this incoming message, decide what action to take. Reference your system prompt to understand your
        purpose and then use your tools and the contents of this message to decide what action to take (if any)
        """

        # Standard BeauchBot tools
        tools = [
            list_google_documents,
            read_google_document, 
            get_conversation_history,
            text_me,
            send_text_dry if os.getenv('TWILIO_WEBHOOK_DEBUG') == 'true' else send_text,
            get_phone_numbers,
            get_current_time
        ]

        # Instantiate the AI agent using factory
        agent = create_beauchbot_agent(
            system_prompt=f"""
            You are a responsive AI agent that has been activated by an incoming ping/message. You share a system with an hourly agent that executes scheduled tasks, but you have a different role.
            Context Awareness
            You have access to the hourly agent's instructions for reference only:
            HOURLY AGENT INSTRUCTIONS (FOR CONTEXT ONLY - DO NOT EXECUTE):
            {get_system_prompt_from_google_doc()}
            Your Role

            PRIMARY FUNCTION: Respond to the incoming ping/message that activated you
            CONTEXT USE: Use the hourly agent's instructions as background context to better understand:

            The overall system's purpose and goals
            Relevant data sources, APIs, or tools available
            Key metrics, processes, or domains the system monitors
            How your response might complement or relate to the scheduled operations

            Important Constraints

            DO NOT execute any of the hourly agent's scheduled tasks
            DO NOT perform any recurring/scheduled operations
            DO NOT initiate any automated processes described in the hourly instructions
            Focus solely on responding to the immediate ping/message
            """,
            tools=tools,
            add_base_tools=True
        )
        
        # Process the message through the agent
        logger.info("Processing message through AI agent...")
        
        agent_response = await Runner.run(agent, message_context)
        
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
