import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from twilio.rest import Client

from mcp_server.server import beauchbot_mcp

logger = logging.getLogger(__name__)


def get_twilio_client():
    """Get Twilio client."""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables are required")
    
    return Client(account_sid, auth_token)


@beauchbot_mcp.tool()
def send_text(to_number: str, message: str) -> Dict[str, Any]:
    """
    Send a text message via Twilio.
    
    Args:
        to_number: The phone number to send to (e.g., "+1234567890")
        message: The message content
        from_number: The Twilio phone number to send from (optional, uses default if not provided)
        
    Returns:
        Message status information
    """
    try:
        client = get_twilio_client()
        
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not from_number:
            raise ValueError("TWILIO_PHONE_NUMBER environment variable is required")
        
        logger.info(f"Sending text to {to_number}: {message[:50]}...")
        
        twilio_message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        response = {
            "sid": twilio_message.sid,
            "status": twilio_message.status,
            "to": twilio_message.to,
            "from": twilio_message.from_,
            "body": twilio_message.body,
            "date_created": twilio_message.date_created.isoformat(),
            "error_code": twilio_message.error_code,
            "error_message": twilio_message.error_message
        }
        
        logger.info(f"Text message sent successfully with SID: {response['sid']}")
        return response
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Error sending text: {e}")
        return {"error": f"Failed to send text: {str(e)}"}


@beauchbot_mcp.tool()
def get_messages(limit: int = 20, date_sent_after: str = None) -> List[Dict[str, Any]]:
    """
    Get messages from Twilio account.
    
    Args:
        limit: Maximum number of messages to return (default: 20)
        date_sent_after: ISO date string to filter messages after this date (optional)
        
    Returns:
        List of message information
    """
    try:
        client = get_twilio_client()
        
        filters = {'limit': limit}
        if date_sent_after:
            # Parse the ISO date string and convert to datetime
            date_obj = datetime.fromisoformat(date_sent_after.replace('Z', '+00:00'))
            filters['date_sent_after'] = date_obj
        
        logger.info(f"Getting messages (limit: {limit}, date_sent_after: {date_sent_after})")
        
        messages = client.messages.list(**filters)
        
        result = [
            {
                "sid": msg.sid,
                "status": msg.status,
                "to": msg.to,
                "from": msg.from_,
                "body": msg.body,
                "date_created": msg.date_created.isoformat(),
                "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                "direction": msg.direction,
                "error_code": msg.error_code,
                "error_message": msg.error_message
            }
            for msg in messages
        ]
        
        logger.info(f"Found {len(result)} messages")
        return result
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return [{"error": str(e)}]
    
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return [{"error": f"Failed to get messages: {str(e)}"}] 