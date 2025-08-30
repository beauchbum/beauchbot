"""
Twilio tools for BeauchBot.

Provides functionality to:
- Send individual SMS and Group MMS messages
- Get conversation history for individuals and groups
- Get contact phone numbers
"""

import os
import logging
import re
from typing import List, Dict, Any

# OpenAI Agents
from agents import function_tool

# Twilio
from twilio.rest import Client

# Import shared phone utilities
from utils.phone_utils import validate_phone_numbers_against_contacts, format_contact_list_for_error

logger = logging.getLogger(__name__)


def get_twilio_client():
    """Initialize and return a Twilio client using environment variables."""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        raise ValueError(
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables are required"
        )
    
    return Client(account_sid, auth_token)


def get_twilio_phone_number() -> str:
    """Get the Twilio phone number from environment variables."""
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not twilio_number:
        raise ValueError("TWILIO_PHONE_NUMBER environment variable is required")
    
    return twilio_number


def get_my_phone_number() -> str:
    """Get my personal phone number from environment variables."""
    my_number = os.getenv('MY_PHONE_NUMBER')
    
    if not my_number:
        raise ValueError("MY_PHONE_NUMBER environment variable is required")
    
    return my_number


@function_tool
def send_text(to_numbers: List[str], message: str) -> Dict[str, Any]:
    """Send a text message to an individual or group via Twilio.

    For individual messaging (1 number): Standard SMS between you and one recipient
    For group messaging (2+ numbers): Creates Group MMS where all participants see each other's messages
    Group MMS requires US/Canada (+1) numbers and creates true group conversations.
    Automatically reuses existing conversations with the same participants to avoid conflicts.
    
    Args:
        to_numbers: List of phone numbers to send to in E.164 format (e.g., ['+12345678901'] for individual or ['+12345678901', '+19876543210'] for group)
        message: The message content to send
    
    Returns:
        Message status information or group conversation details including 'reused_existing' flag
    """
    try:
        if not to_numbers or len(to_numbers) == 0:
            return {"error": "At least one phone number is required"}
        
        # Validate phone numbers against allowed contacts
        valid_numbers, invalid_numbers, matching_contacts = validate_phone_numbers_against_contacts(to_numbers)
        
        if invalid_numbers:
            # Get full contact list for error message
            from utils.phone_utils import get_allowed_contacts
            all_contacts = get_allowed_contacts()
            contact_list = format_contact_list_for_error(all_contacts)
            
            error_msg = f"Cannot send messages to unauthorized phone numbers: {', '.join(invalid_numbers)}\n\n{contact_list}"
            return {"error": error_msg}
        
        if not valid_numbers:
            return {"error": "No valid phone numbers provided"}
        
        client = get_twilio_client()
        from_number = get_twilio_phone_number()
        
        # Log the validated contacts
        contact_names = [contact['name'] for contact in matching_contacts]
        logger.info(f"Sending message to validated contacts: {', '.join(contact_names)}")
        
        # Determine if this is individual or group messaging based on recipient count
        if len(valid_numbers) == 1:
            # Individual messaging using standard SMS
            return _send_individual_text(client, from_number, valid_numbers[0], message)
        else:
            # Group messaging using Group MMS
            return _send_group_text(client, from_number, valid_numbers, message)
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Error sending text: {e}")
        return {"error": f"Failed to send text: {str(e)}"}
    
@function_tool
def send_text_dry(to_numbers: List[str], message: str) -> Dict[str, Any]:
    """Send a text message to a group via Twilio. This is a dry run tool that will not send a message to the group.
    Use this message when you would have used the send_text tool, but you want to see what the message would look like before sending it.

    Args:
        to_numbers: List of phone numbers to send to in E.164 format (e.g., ['+12345678901'] for individual or ['+12345678901', '+19876543210'] for group)
        message: The message content to send

    Returns:
        A dictionary with the message content and status
    """
    return {"debug": "This is a dry run tool that will not send a message to the group.", "to_numbers": to_numbers, "message": message, "status": "dry_run"}

@function_tool
def get_conversation_history(identifier: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get conversation history for either an individual phone number or a group conversation.
    
    Use the get_phone_numbers tool to get a list of contacts with their names and phone numbers for Twilio interactions.
    For individual chats: Provide a phone number in E.164 format (e.g., "+1234567890")
    For group chats: Provide a conversation SID starting with 'CH' (e.g., "CHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    
    Args:
        identifier: Phone number in E.164 format (e.g., '+1234567890') for individual chat, or conversation SID (CHxxx) for group chat
        limit: Maximum number of messages to return (default: 20)
    
    Returns:
        List of messages in the conversation, sorted by date (most recent first)
    """
    try:
        if not identifier.strip():
            return [{"error": "Phone number or conversation SID is required"}]
        
        client = get_twilio_client()
        
        # Determine if this is a conversation SID or phone number
        if identifier.startswith('CH') and len(identifier) == 34:
            # This is a conversation SID - get group conversation history
            return _get_group_conversation_history(client, identifier, limit)
        else:
            # This is a phone number - get individual conversation history
            return _get_individual_conversation_history(client, identifier, limit)
            
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return [{"error": f"Failed to get conversation history: {str(e)}"}]


@function_tool
def text_me(message: str) -> Dict[str, Any]:
    """Send a text message to my personal phone number via Twilio.
    
    This tool uses the TWILIO_PHONE_NUMBER environment variable as the sender 
    and MY_PHONE_NUMBER environment variable as the recipient.
    
    Args:
        message: The message content to send to my phone
    
    Returns:
        Message status information
    """
    try:
        if not message.strip():
            return {"error": "Message content is required"}
        
        client = get_twilio_client()
        from_number = get_twilio_phone_number()
        to_number = get_my_phone_number()
        
        # Send SMS using standard Twilio messaging
        message_result = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        response = {
            "type": "text_me",
            "message_sid": message_result.sid,
            "to": to_number,
            "from": from_number,
            "body": message,
            "status": message_result.status,
            "date_created": message_result.date_created.isoformat() if message_result.date_created else None
        }
        
        logger.info(f"Text message sent to personal number, Message: {message_result.sid}")
        return response
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Error sending text message: {e}")
        return {"error": f"Failed to send text message: {str(e)}"}


# ============================================================================
# HELPER FUNCTIONS (Internal)
# ============================================================================

def _send_individual_text(client, from_number: str, to_number: str, message: str) -> Dict[str, Any]:
    """Send individual SMS message."""
    
    # Send SMS using standard Twilio messaging
    message_result = client.messages.create(
        body=message,
        from_=from_number,
        to=to_number
    )
    
    response = {
        "type": "individual",
        "message_sid": message_result.sid,
        "to": to_number,
        "from": from_number,
        "body": message,
        "status": message_result.status,
        "date_created": message_result.date_created.isoformat() if message_result.date_created else None
    }
    
    logger.info(f"Individual SMS sent to {to_number}, Message: {message_result.sid}")
    return response


def _find_existing_group_conversation(client, target_participants: List[str]) -> Dict[str, Any]:
    """Find an existing Group MMS conversation with the same participants."""
    try:
        # Get recent conversations to check
        conversations = client.conversations.v1.conversations.list(limit=50)
        
        # Convert target participants to a set for comparison
        target_set = set(target_participants)
        
        for conversation in conversations:
            try:
                # Skip if conversation is not active
                if conversation.state != 'active':
                    continue
                
                # Get participants for this conversation
                participants = client.conversations.v1.conversations(conversation.sid).participants.list()
                
                # Extract phone numbers from participants
                participant_numbers = set()
                business_participant = None
                
                for participant in participants:
                    if participant.messaging_binding:
                        # SMS participant - has address
                        if hasattr(participant.messaging_binding, 'address') and participant.messaging_binding.address:
                            participant_numbers.add(participant.messaging_binding.address)
                        elif isinstance(participant.messaging_binding, dict) and participant.messaging_binding.get('address'):
                            participant_numbers.add(participant.messaging_binding['address'])
                    
                    # Track business participant
                    if participant.identity == "beauchbot_assistant":
                        business_participant = participant

                # Check if this conversation has the same SMS participants
                if participant_numbers == target_set:
                    logger.info(f"Found matching conversation: {conversation.sid}")
                    return {
                        "sid": conversation.sid,
                        "friendly_name": conversation.friendly_name,
                        "participants": list(participant_numbers),
                        "business_participant": business_participant.sid if business_participant else None
                    }
                    
            except Exception as e:
                logger.warning(f"Error checking conversation {conversation.sid}: {e}")
                continue
        
        logger.info("No existing conversation found with matching participants")
        return None
        
    except Exception as e:
        logger.error(f"Error finding existing group conversation: {e}")
        return None


def _send_group_text(client, from_number: str, to_numbers: List[str], message: str) -> Dict[str, Any]:
    """Send Group MMS message using Conversations API."""
    try:
        # Validate US/Canada numbers (Group MMS requirement)
        for phone_number in to_numbers:
            if not phone_number.startswith('+1'):
                return {"error": f"Group MMS only supports US/Canada (+1) numbers. Invalid: {phone_number}"}
        
        # Check if there's already an existing conversation with the same participants
        existing_conversation = _find_existing_group_conversation(client, to_numbers)
        
        if existing_conversation:
            logger.info(f"Found existing Group MMS conversation: {existing_conversation['sid']}")
            
            # Ensure beauchbot_assistant participant exists in the conversation
            try:
                # Check if beauchbot_assistant is already a participant
                participants = client.conversations.v1.conversations(existing_conversation['sid']).participants.list()
                beauchbot_participant_exists = any(p.identity == "beauchbot_assistant" for p in participants)
                
                if not beauchbot_participant_exists:
                    logger.info("Adding beauchbot_assistant participant to existing conversation")
                    # Add beauchbot_assistant as chat participant
                    client.conversations.v1.conversations(existing_conversation['sid']).participants.create(
                        identity="beauchbot_assistant",
                        messaging_binding_projected_address=from_number
                    )
                
                # Now send the message
                message_result = client.conversations.v1.conversations(existing_conversation['sid']).messages.create(
                    body=message,
                    author="beauchbot_assistant"
                )
                
                response = {
                    "type": "group",
                    "conversation_sid": existing_conversation['sid'],
                    "message_sid": message_result.sid,
                    "reused_existing": True,
                    "existing_participants": existing_conversation['participants'],
                    "body": message,
                    "date_created": message_result.date_created.isoformat() if message_result.date_created else None
                }
                
                logger.info(f"Group MMS sent to existing conversation: {existing_conversation['sid']}, Message: {message_result.sid}")
                return response
                
            except Exception as e:
                logger.error(f"Failed to send message to existing conversation: {e}")
                # Fall back to creating a new conversation
                logger.info("Falling back to creating new conversation...")

        # Create new conversation
        logger.info(f"Creating new Group MMS conversation with {len(to_numbers)} participants")
        
        # Create conversation
        conversation = client.conversations.v1.conversations.create(
            friendly_name=f"Group conversation {len(to_numbers)} participants"
        )
        
        # Add SMS participants using Group MMS setup (no proxy address)
        participants_added = []
        participants_failed = []
        
        for to_number in to_numbers:
            try:
                # Group MMS: SMS participants have ONLY address, NO proxy address
                participant = client.conversations.v1.conversations(conversation.sid).participants.create(
                    messaging_binding_address=to_number
                )
                
                participants_added.append({
                    "phone_number": to_number,
                    "participant_sid": participant.sid
                })
                
            except Exception as e:
                logger.error(f"Failed to add participant {to_number}: {e}")
                participants_failed.append({
                    "phone_number": to_number,
                    "error": str(e)
                })
        
        # Add business chat participant with projected address
        try:
            chat_participant = client.conversations.v1.conversations(conversation.sid).participants.create(
                identity="beauchbot_assistant",
                messaging_binding_projected_address=from_number
            )
            
            participants_added.append({
                "phone_number": f"BeauchBot (projected: {from_number})",
                "participant_sid": chat_participant.sid
            })
            
        except Exception as e:
            logger.error(f"Failed to add chat participant: {e}")
            participants_failed.append({
                "phone_number": "BeauchBot",
                "error": str(e)
            })
        
        # Send the message as BeauchBot
        if len(participants_added) > 0:
            message_result = client.conversations.v1.conversations(conversation.sid).messages.create(
                body=message,
                author="beauchbot_assistant"
            )
            
            response = {
                "type": "group",
                "conversation_sid": conversation.sid,
                "message_sid": message_result.sid,
                "reused_existing": False,
                "participants_added": participants_added,
                "participants_failed": participants_failed,
                "body": message,
                "date_created": message_result.date_created.isoformat() if message_result.date_created else None
            }
            
            logger.info(f"Group MMS sent successfully to conversation: {conversation.sid}, Message: {message_result.sid}")
            return response
        else:
            return {"error": "Failed to add any participants to the group conversation"}
            
    except Exception as e:
        logger.error(f"Error sending group text: {e}")
        return {"error": f"Failed to send group text: {str(e)}"}


def _get_individual_conversation_history(client, phone_number: str, limit: int) -> List[Dict[str, Any]]:
    """Get conversation history for individual SMS messages."""
    try:
        from_number = get_twilio_phone_number()
        
        # Get messages between our Twilio number and the target number
        messages = client.messages.list(
            limit=limit,
            from_=phone_number,
            to=from_number
        )
        
        # Get messages we sent to them
        sent_messages = client.messages.list(
            limit=limit,
            from_=from_number,
            to=phone_number
        )
        
        # Combine and sort by date
        all_messages = list(messages) + list(sent_messages)
        all_messages.sort(key=lambda x: x.date_created, reverse=True)
        
        # Limit to the requested number
        all_messages = all_messages[:limit]
        
        # Format the messages
        formatted_messages = []
        for msg in all_messages:
            formatted_messages.append({
                "message_sid": msg.sid,
                "from": msg.from_,
                "to": msg.to,
                "body": msg.body,
                "direction": "outbound" if msg.from_ == from_number else "inbound",
                "status": msg.status,
                "date_created": msg.date_created.isoformat() if msg.date_created else None,
                "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                "type": "individual"
            })
        
        logger.info(f"Retrieved {len(formatted_messages)} individual messages for {phone_number}")
        return formatted_messages
        
    except Exception as e:
        logger.error(f"Error getting individual conversation history: {e}")
        return [{"error": f"Failed to get individual conversation history: {str(e)}"}]


def _get_group_conversation_history(client, conversation_sid: str, limit: int) -> List[Dict[str, Any]]:
    """Get conversation history for group conversations."""
    try:
        # Get messages from the conversation
        messages = client.conversations.v1.conversations(conversation_sid).messages.list(
            limit=limit,
            order='desc'
        )
        
        # Format the messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "message_sid": msg.sid,
                "conversation_sid": conversation_sid,
                "author": msg.author,
                "body": msg.body,
                "participant_sid": msg.participant_sid,
                "date_created": msg.date_created.isoformat() if msg.date_created else None,
                "type": "group"
            })
        
        logger.info(f"Retrieved {len(formatted_messages)} group messages for conversation {conversation_sid}")
        return formatted_messages
        
    except Exception as e:
        logger.error(f"Error getting group conversation history: {e}")
        return [{"error": f"Failed to get group conversation history: {str(e)}"}]