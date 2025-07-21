# BeauchBot MCP Server

This MCP server provides various tools and utilities for the BeauchBot system.

## Available Tools

### System Tools
- `get_current_time()` - Get the current date and time in ISO format

### Calendar Tools
- `read_calendar()` - Read the content of your calendar document

### Messaging Tools
- `send_text(to_number, message, from_number=None)` - Send text message via Twilio
- `get_messages(limit=20, date_sent_after=None)` - Get messages from Twilio account

### Contact Tools
- `get_contact(name)` - Get contact information by name (supports partial matching)
- `list_contacts()` - Get all available contacts
- `get_phone_number(name)` - Get just the phone number for a contact by name

## Available Resources

Resources provide read-only data that can be accessed by MCP clients:

- `beauchbot://contacts` - All contact information
- `beauchbot://tools` - List of available tools and their descriptions

## Setup

### Basic Setup
1. Install dependencies:
   ```bash
   poetry install
   ```

2. Start the MCP server:
   ```bash
   poetry run python -m mcp_server.main
   ```

### Twilio Messaging Setup

To use the messaging tools, you'll need to set up your Twilio account and configure the environment variables.

1. **Get Twilio credentials:**
   - Sign up for a [Twilio account](https://www.twilio.com/)
   - Get a Twilio phone number
   - Find your Account SID and Auth Token in the Twilio Console

2. **Set environment variables:**
   ```bash
   export TWILIO_ACCOUNT_SID="your_account_sid"
   export TWILIO_AUTH_TOKEN="your_auth_token"
   export TWILIO_PHONE_NUMBER="your_twilio_phone_number"  # e.g., "+1234567890"
   ```

3. **Usage examples:**
   ```python
   # Send a text message
   result = send_text(
       to_number="+1234567890",
       message="Hello from BeauchBot!"
   )
   
   # Get recent messages
   messages = get_messages(limit=10)
   
   # Get messages from the last day
   from datetime import datetime, timedelta
   yesterday = (datetime.now() - timedelta(days=1)).isoformat()
       messages = get_messages(limit=50, date_sent_after=yesterday)
    ```

### Contact Management

The contact system allows the agent to easily send messages to people by name rather than remembering phone numbers.

**Current contacts:**
- Ryan: +12035839125

**Usage examples:**
```python
# Get contact info by name
contact = get_contact("Ryan")
# Returns: {"name": "Ryan", "phone": "+12035839125", "notes": "Owner/Primary contact"}

# Get just the phone number
phone_info = get_phone_number("Ryan") 
# Returns: {"name": "Ryan", "phone": "+12035839125"}

# Send a text using contact name
contact = get_contact("Ryan")
if "error" not in contact:
    result = send_text(contact["phone"], "Hello!")

# List all contacts
all_contacts = list_contacts()
```

**Adding more contacts:**
To add more contacts, edit the `CONTACTS` list in `mcp_server/resources.py`:

```python
CONTACTS = [
    {
        "name": "Ryan",
        "phone": "+12035839125", 
        "notes": "Owner/Primary contact"
    },
    {
        "name": "John Doe",
        "phone": "+1234567890",
        "notes": "Friend"
    }
]
```

### Calendar Tool Setup

The calendar tool reads from a specific Google Doc that contains your calendar events.

#### Step 1: Create a Service Account

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Docs API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Docs API"
   - Click "Enable"
4. Create a service account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and create the account
5. Generate a key for the service account:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format and download

#### Step 2: Set Up Authentication

**For Local Development:**
```bash
export GOOGLE_SERVICE_ACCOUNT_B64=$(python scripts/encode_service_account.py path/to/service-account.json)
export CALENDAR_DOC_ID="your_calendar_document_id"
```

**For Production (Render):**
1. Run the encoding script:
   ```bash
   python scripts/encode_service_account.py path/to/service-account.json
   ```
2. Copy the base64 string and document ID from the output
3. Add environment variables in Render dashboard:
   - **Key**: `GOOGLE_SERVICE_ACCOUNT_B64`
   - **Value**: The base64 encoded string
   - **Key**: `CALENDAR_DOC_ID`
   - **Value**: Your calendar document ID

#### Step 3: Share Your Calendar Document

- Copy the `client_email` from your service account JSON (shown in the encoder output)
- Share your calendar Google Doc with this email address
- Give it "Viewer" permissions

**Security Note**: Never commit your service account JSON file to version control. Always use the base64 encoded environment variable.

#### Step 4: Get Your Calendar Document ID

You can find your calendar document ID from the URL:
- Open your calendar document in Google Docs
- Look at the URL: `https://docs.google.com/document/d/DOCUMENT_ID/edit`
- The `DOCUMENT_ID` part is what you need

#### Step 5: Test Your Setup

Test that everything is working:

```bash
# Test authentication and calendar access
python scripts/test_google_docs.py
```

## Usage

### Reading Your Calendar

Simply call the tool without any parameters:

```python
# Read your calendar
calendar_content = read_calendar()
```

The tool will automatically read from the document specified in your `CALENDAR_DOC_ID` environment variable.

## Troubleshooting

### Calendar Tool Issues

- **"GOOGLE_SERVICE_ACCOUNT_B64 environment variable is required"**: Run the encoder script and set the environment variable
- **"CALENDAR_DOC_ID environment variable is required"**: Set the `CALENDAR_DOC_ID` environment variable to your document ID
- **"Access denied"**: Make sure the service account has read access to your calendar document
- **"Calendar document not found"**: Verify the document ID is correct and the document exists

### Permission Issues

Share your calendar document with the service account email address with "Viewer" permissions.

### Twilio Issues

- **"TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables are required"**: Set your Twilio credentials in environment variables
- **"TWILIO_PHONE_NUMBER environment variable is required"**: Set your Twilio phone number (must include country code, e.g., "+1234567890")
- **"The number ... is unverified"**: In Twilio trial accounts, you can only send to verified phone numbers
- **"Invalid phone number format"**: Ensure phone numbers include the country code and are in E.164 format (e.g., "+1234567890")
- **Message delivery failures**: Check the message status and error codes in the response for specific failure reasons

### API Quotas

- Google Docs API has usage quotas. If you hit limits, requests will fail with quota exceeded errors
- Twilio has rate limits and usage quotas depending on your account type
- For production use, consider implementing rate limiting and caching 