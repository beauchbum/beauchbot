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
from typing import Dict, Any, List

# SmolAgents
from smolagents import Tool

# Google APIs
from googleapiclient.errors import HttpError

# Import shared Google utilities
from utils.google_utils import get_google_docs_service, get_google_drive_service, extract_text_from_document

logger = logging.getLogger(__name__)


def get_google_service():
    """Get Google Docs service - wrapper for backward compatibility."""
    return get_google_docs_service()


class ListGoogleDocumentsTool(Tool):
    name = "list_google_documents"
    description = """List Google Documents that the service account has access to. 
    Returns a list of documents with their ID, name, modified time, and owner information.
    Use this to browse available documents before reading specific ones."""
    inputs = {
        "limit": {
            "type": "integer", 
            "description": "Maximum number of documents to return (default: 20, max: 100)",
            "nullable": True
        }
    }
    output_type = "array"

    def forward(self, limit: int = 20) -> List[Dict[str, Any]]:
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


class ReadGoogleDocumentTool(Tool):
    name = "read_google_document"
    description = """Read the content of any Google Document by its ID. 
    The document ID can be found in the URL or obtained from list_google_documents.
    Returns the complete text content of the document including the title."""
    inputs = {
        "document_id": {
            "type": "string",
            "description": "The Google Document ID (e.g., '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms')"
        }
    }
    output_type = "string"

    def forward(self, document_id: str) -> str:
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
        

class GetPhoneNumbersTool(Tool):
    name = "get_phone_numbers"
    description = """Read the content of the phone directory document. 
    The phone directory document ID must be set in the PHONE_DIRECTORY_DOC_ID environment variable.
    Returns the complete text content of the phone directory document. This provides a list of names and phone numbers for messaging."""
    inputs = {}
    output_type = "string"

    def forward(self) -> str:
        try:
            # Get the phone directory document ID from environment variable 
            phone_directory_doc_id = os.getenv('PHONE_DIRECTORY_DOC_ID')
            
            if not phone_directory_doc_id:
                return "Error: PHONE_DIRECTORY_DOC_ID environment variable is required. Please set it to your phone directory document ID."
            
            # Get the Google Docs service
            service = get_google_service()
            
            # Retrieve the document
            document = service.documents().get(documentId=phone_directory_doc_id).execute()

            # Extract text content
            text_content = extract_text_from_document(document)
            
            # Get document metadata
            title = document.get('title', 'Phone Directory')
            
            result = f"# {title}\n\n{text_content}"
            
            logger.info(f"Successfully read phone directory document: {title} (ID: {phone_directory_doc_id})")
            return result
        
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            error_message = error_details.get('error', {}).get('message', 'Unknown error')
            
            if e.resp.status == 403:
                return f"Error: Access denied. Make sure the service account has permission to read the phone directory document. Details: {error_message}"
            elif e.resp.status == 404:
                return f"Error: Phone directory document not found. Please check the PHONE_DIRECTORY_DOC_ID environment variable. Details: {error_message}"
            else:
                return f"Error: Google API error (status {e.resp.status}): {error_message}"
        
        except ValueError as e:
            return f"Error: {str(e)}"
        
        except Exception as e:
            logger.error(f"Unexpected error reading phone directory: {e}")
            return f"Error: Unexpected error occurred: {str(e)}"