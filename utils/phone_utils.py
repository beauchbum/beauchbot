"""
Phone number utilities for BeauchBot.

Provides shared functionality for:
- Phone number parsing and validation
- Contact management
- Phone number normalization
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_phone_numbers_from_text(text_content: str) -> List[Dict[str, str]]:
    """
    Parse phone numbers and names from text content.
    
    Expected format: "Name: Phone Number" on each line
    This function is resilient to formatting variations like:
    - Extra whitespace
    - Different separators (: or -)
    - Various phone number formats
    - Empty lines
    
    Args:
        text_content: Raw text content from the document
        
    Returns:
        List of dictionaries with 'name' and 'phone_number' keys
    """
    contacts = []
    
    # Split by lines and process each line
    lines = text_content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Skip lines that look like headers or section dividers
        if line.startswith('#') or line.startswith('---') or line.lower() in ['phone directory', 'contacts', 'numbers']:
            continue
        
        # Try to match patterns like "Name: Phone" or "Name - Phone"
        # This regex looks for: characters before separator, then separator (: or - variants), then phone content
        pattern = r'^([^:–—-]+?)[\s]*[:–—-][\s]*(.+)$'
        match = re.match(pattern, line)
        
        if match:
            name_part = match.group(1).strip()
            phone_part = match.group(2).strip()
            
            # Basic validation - name should have at least 2 characters
            if len(name_part) < 2:
                continue
                
            # Basic phone validation - should contain digits
            if not re.search(r'\d', phone_part):
                continue
                
            # Clean up the phone number - remove common formatting but preserve the content
            # This handles formats like: (555) 123-4567, +1-555-123-4567, 555.123.4567, etc.
            cleaned_phone = re.sub(r'[^\d+]', '', phone_part)
            
            # If phone starts with 1 and has 11 digits, format as +1XXXXXXXXXX
            if cleaned_phone.startswith('1') and len(cleaned_phone) == 11:
                formatted_phone = f"+{cleaned_phone}"
            # If phone has 10 digits, assume US number and add +1
            elif len(cleaned_phone) == 10 and cleaned_phone.isdigit():
                formatted_phone = f"+1{cleaned_phone}"
            # If phone already has + or is international format, keep as is
            elif cleaned_phone.startswith('+'):
                formatted_phone = cleaned_phone
            else:
                # Keep original phone format if we can't determine the proper format
                formatted_phone = phone_part
            
            contacts.append({
                'name': name_part,
                'phone_number': formatted_phone,
                'original_line': line  # Keep original for debugging
            })
        else:
            # Log lines that don't match expected format for debugging
            logger.debug(f"Could not parse line: '{line}'")
    
    logger.info(f"Parsed {len(contacts)} contacts from phone directory")
    return contacts


def get_allowed_contacts() -> List[Dict[str, str]]:
    """
    Get the list of allowed contacts from the phone directory document.
    
    Returns:
        List of contacts with 'name' and 'phone_number' keys, or empty list on error
    """
    try:
        # Import here to avoid circular imports
        from utils.google_utils import get_google_docs_service, extract_text_from_document
        
        # Get the phone directory document ID from environment variable 
        phone_directory_doc_id = os.getenv('PHONE_DIRECTORY_DOC_ID')
        
        if not phone_directory_doc_id:
            logger.error("PHONE_DIRECTORY_DOC_ID environment variable not set")
            return []
        
        # Get the Google Docs service
        service = get_google_docs_service()
        
        # Retrieve the document
        document = service.documents().get(documentId=phone_directory_doc_id).execute()

        # Extract text content
        text_content = extract_text_from_document(document)
        
        # Parse the text content to extract contacts
        contacts = parse_phone_numbers_from_text(text_content)
        
        logger.info(f"Retrieved {len(contacts)} allowed contacts from phone directory")
        return contacts
        
    except Exception as e:
        logger.error(f"Error retrieving allowed contacts: {e}")
        return []


def validate_phone_numbers_against_contacts(phone_numbers: List[str]) -> Tuple[List[str], List[str], List[Dict[str, str]]]:
    """
    Validate a list of phone numbers against the allowed contacts.
    
    Args:
        phone_numbers: List of phone numbers to validate
        
    Returns:
        Tuple of (valid_numbers, invalid_numbers, matching_contacts)
    """
    # Get allowed contacts
    allowed_contacts = get_allowed_contacts()
    
    if not allowed_contacts:
        logger.warning("No allowed contacts found - validation will fail")
        return [], phone_numbers, []
    
    # Create a set of allowed phone numbers for fast lookup
    allowed_numbers = {contact['phone_number'] for contact in allowed_contacts}
    
    valid_numbers = []
    invalid_numbers = []
    matching_contacts = []
    
    for phone_number in phone_numbers:
        if phone_number in allowed_numbers:
            valid_numbers.append(phone_number)
            # Find the matching contact
            matching_contact = next(
                (contact for contact in allowed_contacts if contact['phone_number'] == phone_number),
                None
            )
            if matching_contact:
                matching_contacts.append(matching_contact)
        else:
            invalid_numbers.append(phone_number)
    
    logger.info(f"Phone validation: {len(valid_numbers)} valid, {len(invalid_numbers)} invalid")
    return valid_numbers, invalid_numbers, matching_contacts


def format_contact_list_for_error(contacts: List[Dict[str, str]]) -> str:
    """
    Format a list of contacts for display in error messages.
    
    Args:
        contacts: List of contact dictionaries
        
    Returns:
        Formatted string showing available contacts
    """
    if not contacts:
        return "No contacts available. Please check the phone directory document."
    
    # Sort contacts by name for better presentation
    sorted_contacts = sorted(contacts, key=lambda c: c['name'].lower())
    
    contact_lines = []
    for contact in sorted_contacts:
        contact_lines.append(f"  - {contact['name']}: {contact['phone_number']}")
    
    return f"Available contacts:\n" + "\n".join(contact_lines)
