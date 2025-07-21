import os
import json
import base64
import logging
from typing import Dict, Any, List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp_server.server import beauchbot_mcp

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]


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


def get_google_drive_service():
    """Get Google Drive service with service account authentication."""
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
        
        logger.info(f"Using service account for Drive: {service_account_info.get('client_email', 'unknown')}")
        
        return build('drive', 'v3', credentials=creds)
        
    except Exception as e:
        raise ValueError(f"Failed to decode service account credentials: {e}")


def get_google_sheets_service():
    """Get Google Sheets service with service account authentication."""
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
        
        logger.info(f"Using service account for Sheets: {service_account_info.get('client_email', 'unknown')}")
        
        return build('sheets', 'v4', credentials=creds)
        
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
def list_google_documents(limit: int = 20) -> List[Dict[str, Any]]:
    """
    List Google Documents that the service account has access to.
    
    Args:
        limit: Maximum number of documents to return (default: 20, max: 100)
        
    Returns:
        List of documents with their ID, name, modified time, and owner information
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


@beauchbot_mcp.tool()
def list_google_sheets(limit: int = 20) -> List[Dict[str, Any]]:
    """
    List Google Sheets that the service account has access to.
    
    Args:
        limit: Maximum number of sheets to return (default: 20, max: 100)
        
    Returns:
        List of spreadsheets with their ID, name, modified time, and owner information
    """
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20
            
        logger.info(f"Listing Google Sheets (limit: {limit})")
        
        # Get Google Drive service
        drive_service = get_google_drive_service()
        
        # Query for Google Sheets only
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet'",
            pageSize=limit,
            fields="files(id,name,modifiedTime,owners,webViewLink,createdTime,shared)",
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        
        spreadsheets = []
        for file in files:
            sheet_info = {
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
                sheet_info['owner'] = owners[0].get('displayName', 'Unknown')
                sheet_info['owner_email'] = owners[0].get('emailAddress', 'Unknown')
            else:
                sheet_info['owner'] = 'Unknown'
                sheet_info['owner_email'] = 'Unknown'
                
            spreadsheets.append(sheet_info)
        
        logger.info(f"Found {len(spreadsheets)} Google Sheets")
        return spreadsheets
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get('error', {}).get('message', 'Unknown error')
        
        logger.error(f"Google Drive API error: {error_message}")
        return [{"error": f"Google Drive API error: {error_message}"}]
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return [{"error": str(e)}]
    
    except Exception as e:
        logger.error(f"Unexpected error listing sheets: {e}")
        return [{"error": f"Unexpected error occurred: {str(e)}"}]


@beauchbot_mcp.tool()
def read_google_document(document_id: str) -> str:
    """
    Read the content of any Google Document by its ID.
    
    Args:
        document_id: The Google Document ID (can be found in the URL or from list_google_documents)
        
    Returns:
        The text content of the document
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


@beauchbot_mcp.tool()
def read_google_sheet(spreadsheet_id: str, sheet_name: str = None, range_name: str = None) -> str:
    """
    Read the content of a Google Sheet by its ID.
    
    Args:
        spreadsheet_id: The Google Sheets ID (can be found in the URL or from list_google_sheets)
        sheet_name: Name of the specific sheet/tab to read (optional, defaults to first sheet)
        range_name: Specific range to read like 'A1:E10' (optional, defaults to all data)
        
    Returns:
        The content of the sheet formatted as text with sheet information
    """
    try:
        if not spreadsheet_id.strip():
            return "Error: Spreadsheet ID is required"
            
        logger.info(f"Reading Google Sheet: {spreadsheet_id}")
        
        # Get Google Sheets service
        sheets_service = get_google_sheets_service()
        
        # Get spreadsheet metadata first
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        title = spreadsheet.get('properties', {}).get('title', 'Untitled Spreadsheet')
        sheets = spreadsheet.get('sheets', [])
        
        if not sheets:
            return f"Error: No sheets found in spreadsheet '{title}'"
        
        # Determine which sheet to read
        target_sheet = None
        if sheet_name:
            # Find sheet by name
            for sheet in sheets:
                if sheet['properties']['title'].lower() == sheet_name.lower():
                    target_sheet = sheet
                    break
            if not target_sheet:
                available_sheets = [s['properties']['title'] for s in sheets]
                return f"Error: Sheet '{sheet_name}' not found. Available sheets: {', '.join(available_sheets)}"
        else:
            # Use first sheet
            target_sheet = sheets[0]
        
        sheet_title = target_sheet['properties']['title']
        
        # Construct range
        if range_name:
            full_range = f"'{sheet_title}'!{range_name}"
        else:
            full_range = f"'{sheet_title}'"
        
        # Read the data
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=full_range
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return f"Spreadsheet: {title}\nSheet: {sheet_title}\n\nNo data found in the specified range."
        
        # Format the data as a readable table
        formatted_output = f"Spreadsheet: {title}\nSheet: {sheet_title}\n"
        if range_name:
            formatted_output += f"Range: {range_name}\n"
        formatted_output += f"\nData ({len(values)} rows):\n" + "="*50 + "\n\n"
        
        # Find the maximum width for each column for better formatting
        max_cols = max(len(row) for row in values) if values else 0
        col_widths = [0] * max_cols
        
        # Calculate column widths
        for row in values:
            for i, cell in enumerate(row):
                if i < max_cols:
                    col_widths[i] = max(col_widths[i], len(str(cell)) if cell else 0)
        
        # Limit column width to reasonable maximum
        col_widths = [min(width, 20) for width in col_widths]
        
        # Format each row
        for row_idx, row in enumerate(values):
            formatted_row = ""
            for col_idx in range(max_cols):
                cell_value = str(row[col_idx]) if col_idx < len(row) and row[col_idx] else ""
                # Truncate if too long
                if len(cell_value) > 20:
                    cell_value = cell_value[:17] + "..."
                formatted_row += cell_value.ljust(col_widths[col_idx] + 2)
            
            formatted_output += formatted_row.rstrip() + "\n"
            
            # Add separator after header row (first row)
            if row_idx == 0 and len(values) > 1:
                separator = ""
                for width in col_widths:
                    separator += "-" * (width + 2)
                formatted_output += separator.rstrip() + "\n"
        
        # Add summary
        if len(values) > 10:
            formatted_output += f"\n... ({len(values)} total rows)"
        
        # List other available sheets if there are any
        if len(sheets) > 1:
            other_sheets = [s['properties']['title'] for s in sheets if s['properties']['title'] != sheet_title]
            if other_sheets:
                formatted_output += f"\n\nOther available sheets: {', '.join(other_sheets)}"
        
        logger.info(f"Successfully read sheet: {title} - {sheet_title}")
        return formatted_output
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get('error', {}).get('message', 'Unknown error')
        
        if e.resp.status == 403:
            return f"Error: Access denied. Make sure the service account has permission to read this spreadsheet. Details: {error_message}"
        elif e.resp.status == 404:
            return f"Error: Spreadsheet not found. Please check the spreadsheet ID. Details: {error_message}"
        else:
            return f"Error: Google Sheets API error (status {e.resp.status}): {error_message}"
    
    except ValueError as e:
        return f"Error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error reading sheet: {e}")
        return f"Error: Unexpected error occurred: {str(e)}"


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