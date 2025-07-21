import logging
from typing import List, Dict, Any, Optional

from mcp_server.server import beauchbot_mcp

logger = logging.getLogger(__name__)

# Import contacts from resources
from mcp_server.resources import CONTACTS


@beauchbot_mcp.tool()
def get_contact(name: str) -> Dict[str, Any]:
    """
    Get contact information by name.
    
    Args:
        name: The name of the contact to search for (case-insensitive)
        
    Returns:
        Contact information including name, phone number, and notes
    """
    try:
        # Search for contact by name (case-insensitive)
        name_lower = name.lower().strip()
        
        for contact in CONTACTS:
            if contact["name"].lower() == name_lower:
                logger.info(f"Found contact: {contact['name']}")
                return contact
        
        # If exact match not found, try partial match
        for contact in CONTACTS:
            if name_lower in contact["name"].lower():
                logger.info(f"Found partial match: {contact['name']}")
                return contact
        
        logger.warning(f"Contact '{name}' not found")
        return {"error": f"Contact '{name}' not found"}
        
    except Exception as e:
        logger.error(f"Error searching for contact '{name}': {e}")
        return {"error": f"Failed to search for contact: {str(e)}"}


@beauchbot_mcp.tool()
def list_contacts() -> List[Dict[str, Any]]:
    """
    Get a list of all available contacts.
    
    Returns:
        List of all contacts with their information
    """
    try:
        logger.info(f"Returning {len(CONTACTS)} contacts")
        return CONTACTS
        
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        return [{"error": f"Failed to list contacts: {str(e)}"}]


@beauchbot_mcp.tool()
def get_phone_number(name: str) -> Dict[str, Any]:
    """
    Get just the phone number for a contact by name.
    
    Args:
        name: The name of the contact
        
    Returns:
        Phone number for the contact
    """
    try:
        contact = get_contact(name)
        
        if "error" in contact:
            return contact
        
        return {
            "name": contact["name"],
            "phone": contact["phone"]
        }
        
    except Exception as e:
        logger.error(f"Error getting phone number for '{name}': {e}")
        return {"error": f"Failed to get phone number: {str(e)}"} 