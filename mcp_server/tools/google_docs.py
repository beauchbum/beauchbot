import os
import json
import base64
import logging
from typing import Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp_server.server import beauchbot_mcp

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']


def get_google_service():
    """Get Google Docs service with service account authentication."""
    service_account_b64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_B64')
    
    if not service_account_b64:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_B64 environment variable is required. "
            "Run 'python scripts/encode_service_account.py path/to/service-account.json' "
            "to generate the base64 encoded service account JSON."
        )
    
    try:
        # Decode base64 and parse JSON
        service_account_json = base64.b64decode(service_account_b64).decode('utf-8')
        service_account_info = json.loads(service_account_json)
        
        # Create credentials
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES)
        
        logger.info(f"Using service account: {service_account_info.get('client_email', 'unknown')}")
        
        return build('docs', 'v1', credentials=creds)
        
    except Exception as e:
        raise ValueError(f"Failed to decode service account credentials: {e}")


def extract_text_from_document(doc_content: Dict[str, Any]) -> str:
    """Extract plain text from Google Docs document structure."""
    def extract_text_from_element(element):
        text = ""
        if 'textRun' in element:
            text += element['textRun']['content']
        elif 'inlineObjectElement' in element:
            # Handle inline objects (images, etc.)
            text += "[INLINE_OBJECT]"
        return text
    
    def extract_text_from_paragraph(paragraph):
        text = ""
        if 'elements' in paragraph:
            for element in paragraph['elements']:
                text += extract_text_from_element(element)
        return text
    
    def extract_text_from_table(table):
        text = ""
        if 'tableRows' in table:
            for row in table['tableRows']:
                if 'tableCells' in row:
                    for cell in row['tableCells']:
                        if 'content' in cell:
                            for content_element in cell['content']:
                                if 'paragraph' in content_element:
                                    text += extract_text_from_paragraph(content_element['paragraph'])
                        text += "\t"  # Tab between cells
                    text += "\n"  # New line after each row
        return text
    
    full_text = ""
    if 'body' in doc_content and 'content' in doc_content['body']:
        for content_element in doc_content['body']['content']:
            if 'paragraph' in content_element:
                full_text += extract_text_from_paragraph(content_element['paragraph'])
            elif 'table' in content_element:
                full_text += extract_text_from_table(content_element['table'])
            elif 'sectionBreak' in content_element:
                full_text += "\n---\n"  # Section break
    
    return full_text.strip()


@beauchbot_mcp.tool()
def read_calendar() -> str:
    """
    Read the content of the calendar document.
    
    Returns:
        The plain text content of the calendar document
    """
    try:
        # Get the calendar document ID from environment variable
        calendar_doc_id = os.getenv('CALENDAR_DOC_ID')
        
        if not calendar_doc_id:
            return "Error: CALENDAR_DOC_ID environment variable is required. Please set it to your calendar document ID."
        
        # Get the Google Docs service
        service = get_google_service()
        
        # Retrieve the document
        document = service.documents().get(documentId=calendar_doc_id).execute()
        
        # Extract text content
        text_content = extract_text_from_document(document)
        
        # Get document metadata
        title = document.get('title', 'Calendar')
        
        result = f"# {title}\n\n{text_content}"
        
        logger.info(f"Successfully read calendar document: {title} (ID: {calendar_doc_id})")
        return result
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get('error', {}).get('message', 'Unknown error')
        
        if e.resp.status == 403:
            return f"Error: Access denied. Make sure the service account has permission to read the calendar document. Details: {error_message}"
        elif e.resp.status == 404:
            return f"Error: Calendar document not found. Please check the CALENDAR_DOC_ID environment variable. Details: {error_message}"
        else:
            return f"Error: Google API error (status {e.resp.status}): {error_message}"
    
    except ValueError as e:
        return f"Error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error reading calendar: {e}")
        return f"Error: Unexpected error occurred: {str(e)}" 