#!/usr/bin/env python3
"""
Helper script to encode Google service account JSON for deployment.

Usage:
    python scripts/encode_service_account.py path/to/service-account.json
"""

import sys
import json
import base64
from pathlib import Path


def encode_service_account(json_path: str) -> str:
    """
    Encode a service account JSON file to base64 for deployment.
    
    Args:
        json_path: Path to the service account JSON file
        
    Returns:
        Base64 encoded string
    """
    try:
        # Read and validate JSON file
        with open(json_path, 'r') as f:
            service_account_data = json.load(f)
        
        # Validate it's a service account file
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in service_account_data]
        
        if missing_fields:
            raise ValueError(f"Invalid service account file. Missing fields: {missing_fields}")
        
        if service_account_data.get('type') != 'service_account':
            raise ValueError("This doesn't appear to be a service account JSON file")
        
        # Convert back to JSON string and encode to base64
        json_string = json.dumps(service_account_data)
        encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        
        return encoded
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Service account file not found: {json_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON file: {json_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/encode_service_account.py path/to/service-account.json")
        print()
        print("This script encodes your Google service account JSON file to base64")
        print("for use in deployment environment variables.")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    try:
        encoded = encode_service_account(json_path)
        
        # Extract service account info for user
        with open(json_path, 'r') as f:
            service_account_data = json.load(f)
        
        print("✅ Service account JSON encoded successfully!")
        print()
        print(f"📋 Service Account Info:")
        print(f"   Email: {service_account_data['client_email']}")
        print(f"   Project: {service_account_data['project_id']}")
        print()
        print("🔐 Environment Variable:")
        print(f"   GOOGLE_SERVICE_ACCOUNT_B64={encoded}")
        print()
        print("📝 Next Steps:")
        print("1. Copy the environment variable above")
        print("2. Add it to your Render dashboard (Environment tab)")
        print("3. Share your Google Docs with the service account email above")
        print("4. Give the service account 'Viewer' permissions")
        print()
        print("⚠️  Security Note: Keep this encoded value secret!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 