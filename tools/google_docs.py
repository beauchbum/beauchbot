"""
Google Docs tools for BeauchBot.

Provides functionality to:
- List Google Documents
- Read Google Document content  
- Read calendar document
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional

# OpenAI Agents
from agents import function_tool

# Google APIs
from googleapiclient.errors import HttpError

# Import shared Google utilities
from utils.google_utils import get_google_docs_service, get_google_drive_service, extract_text_from_document
# Import shared phone utilities
from utils.phone_utils import parse_phone_numbers_from_text

logger = logging.getLogger(__name__)



def get_google_service():
    """Get Google Docs service - wrapper for backward compatibility."""
    return get_google_docs_service()


@function_tool
def list_google_documents(limit: int = 20) -> List[Dict[str, Any]]:
    """List Google Documents that the service account has access to. 
    Returns a list of documents with their ID, name, modified time, and owner information.
    Use this to browse available documents before reading specific ones.
    
    Args:
        limit: Maximum number of documents to return (default: 20, max: 100)
    
    Returns:
        List of document dictionaries with metadata
    """
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20
            
        logger.info(f"Listing Google Documents (limit: {limit})")
        
        # Get Google Drive service
        drive_service = get_google_drive_service()
        
        # Query for Google Documents only
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.document'",
            pageSize=limit,
            fields="files(id,name,modifiedTime,owners,webViewLink,createdTime,size,shared)",
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        
        documents = []
        for file in files:
            doc_info = {
                'id': file['id'],
                'name': file['name'],
                'modified_time': file.get('modifiedTime', 'Unknown'),
                'created_time': file.get('createdTime', 'Unknown'),
                'web_view_link': file.get('webViewLink', ''),
                'shared': file.get('shared', False)
            }
            
            # Add owner information if available
            owners = file.get('owners', [])
            if owners:
                doc_info['owner'] = owners[0].get('displayName', 'Unknown')
                doc_info['owner_email'] = owners[0].get('emailAddress', 'Unknown')
            else:
                doc_info['owner'] = 'Unknown'
                doc_info['owner_email'] = 'Unknown'
                
            documents.append(doc_info)
        
        logger.info(f"Found {len(documents)} Google Documents")
        return documents
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get('error', {}).get('message', 'Unknown error')
        
        logger.error(f"Google Drive API error: {error_message}")
        return [{"error": f"Google Drive API error: {error_message}"}]
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return [{"error": str(e)}]
    
    except Exception as e:
        logger.error(f"Unexpected error listing documents: {e}")
        return [{"error": f"Unexpected error occurred: {str(e)}"}]


@function_tool
def read_google_document(document_id: str) -> str:
    """Read the content of any Google Document by its ID. 
    The document ID can be found in the URL or obtained from list_google_documents.
    Returns the complete text content of the document including the title.
    
    Args:
        document_id: The Google Document ID (e.g., '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms')
    
    Returns:
        Complete text content of the document including title
    """
    try:
        if not document_id.strip():
            return "Error: Document ID is required"
            
        logger.info(f"Reading Google Document: {document_id}")
        
        # Get Google Docs service
        docs_service = get_google_service()
        
        # Retrieve the document
        document = docs_service.documents().get(documentId=document_id).execute()
        
        # Extract text content
        text_content = extract_text_from_document(document)
        
        # Get document title
        title = document.get('title', 'Untitled Document')
        
        result = f"Document: {title}\n\n{text_content}"
        
        logger.info(f"Successfully read document: {title} (ID: {document_id})")
        return result
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get('error', {}).get('message', 'Unknown error')
        
        if e.resp.status == 403:
            return f"Error: Access denied. Make sure the service account has permission to read this document. Details: {error_message}"
        elif e.resp.status == 404:
            return f"Error: Document not found. Please check the document ID. Details: {error_message}"
        else:
            return f"Error: Google API error (status {e.resp.status}): {error_message}"
    
    except ValueError as e:
        return f"Error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error reading document: {e}")
        return f"Error: Unexpected error occurred: {str(e)}"
        

@function_tool
def get_phone_numbers() -> List[Dict[str, str]]:
    """Read and parse the phone directory document to extract structured contact information.
    The phone directory document ID must be set in the PHONE_DIRECTORY_DOC_ID environment variable.
    
    Parses the document content expecting format: "Name: Phone Number" on each line.
    Handles various formatting variations and normalizes phone numbers to E.164 format when possible.
    
    Returns a structured list of contacts with name and phone_number fields for messaging.
    
    Returns:
        List of contact dictionaries with name and phone_number fields
    """
    try:
        # Get the phone directory document ID from environment variable 
        phone_directory_doc_id = os.getenv('PHONE_DIRECTORY_DOC_ID')
        
        if not phone_directory_doc_id:
            return [{"error": "PHONE_DIRECTORY_DOC_ID environment variable is required. Please set it to your phone directory document ID."}]
        
        # Get the Google Docs service
        service = get_google_service()
        
        # Retrieve the document
        document = service.documents().get(documentId=phone_directory_doc_id).execute()

        # Extract text content
        text_content = extract_text_from_document(document)
        
        # Parse the text content to extract contacts
        contacts = parse_phone_numbers_from_text(text_content)
        
        # Get document metadata for logging
        title = document.get('title', 'Phone Directory')
        
        logger.info(f"Successfully parsed {len(contacts)} contacts from phone directory document: {title} (ID: {phone_directory_doc_id})")
        return contacts
    
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get('error', {}).get('message', 'Unknown error')
        
        if e.resp.status == 403:
            return [{"error": f"Access denied. Make sure the service account has permission to read the phone directory document. Details: {error_message}"}]
        elif e.resp.status == 404:
            return [{"error": f"Phone directory document not found. Please check the PHONE_DIRECTORY_DOC_ID environment variable. Details: {error_message}"}]
        else:
            return [{"error": f"Google API error (status {e.resp.status}): {error_message}"}]
    
    except ValueError as e:
        return [{"error": str(e)}]
    
    except Exception as e:
        logger.error(f"Unexpected error reading phone directory: {e}")
        return [{"error": f"Unexpected error occurred: {str(e)}"}]