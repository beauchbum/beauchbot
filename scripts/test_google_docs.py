#!/usr/bin/env python3
"""
Test script for the calendar MCP tool.

Usage:
    python scripts/test_google_docs.py

This script tests the calendar tool authentication and document reading functionality.
"""

import sys
import os
import json
import base64
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the functions directly from the module
from mcp_server.tools.google_docs import (
    get_google_service, 
    extract_text_from_document
)


def test_auth():
    """Test if the authentication is working."""
    print("🔐 Testing Authentication...")
    
    service_account_b64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_B64')
    if not service_account_b64:
        print("❌ GOOGLE_SERVICE_ACCOUNT_B64 environment variable not found")
        print("💡 Run: python scripts/encode_service_account.py path/to/service-account.json")
        return False
    
    try:
        # Try to decode the service account
        service_account_json = base64.b64decode(service_account_b64).decode('utf-8')
        service_account_info = json.loads(service_account_json)
        
        email = service_account_info.get('client_email', 'unknown')
        project = service_account_info.get('project_id', 'unknown')
        
        print(f"✅ Service account found: {email}")
        print(f"📋 Project: {project}")
        
        # Test getting the Google service
        print("   Testing Google API connection...")
        service = get_google_service()
        print("✅ Google API connection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return False


def test_calendar_access():
    """Test accessing the calendar document."""
    print("\n📅 Testing Calendar Access...")
    
    calendar_doc_id = os.getenv('CALENDAR_DOC_ID')
    if not calendar_doc_id:
        print("❌ CALENDAR_DOC_ID environment variable not found")
        print("💡 Set CALENDAR_DOC_ID to your calendar document ID")
        return False
    
    print(f"   Calendar Document ID: {calendar_doc_id}")
    
    try:
        # Get the Google Docs service
        service = get_google_service()
        
        # Test getting calendar document
        print("   Retrieving calendar document...")
        document = service.documents().get(documentId=calendar_doc_id).execute()
        
        title = document.get('title', 'Calendar')
        revision_id = document.get('revisionId', '')
        
        print(f"✅ Calendar document info:")
        print(f"   Title: {title}")
        print(f"   Revision ID: {revision_id}")
        
        # Test reading calendar content
        print("   Reading calendar content...")
        text_content = extract_text_from_document(document)
        
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        print(f"✅ Calendar content read successfully")
        print(f"   Word count: {word_count}")
        print(f"   Character count: {char_count}")
        
        if text_content:
            print(f"   First 200 characters: {text_content[:200]}...")
        else:
            print("   ⚠️  Calendar appears to be empty")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to access calendar: {e}")
        return False


def main():
    print("🚀 Calendar MCP Tool Test")
    print("=" * 40)
    
    # Test authentication
    if not test_auth():
        print("\n❌ Authentication test failed. Please check your setup.")
        return
    
    # Test calendar access
    if test_calendar_access():
        print("\n✅ All tests passed! Calendar tool is working correctly.")
    else:
        print("\n❌ Calendar access test failed.")
        print("💡 Make sure:")
        print("   1. CALENDAR_DOC_ID is set to the correct document ID")
        print("   2. The calendar document exists")
        print("   3. The service account has 'Viewer' permissions")
        print("   4. The calendar document is shared with the service account email")


if __name__ == "__main__":
    main() 