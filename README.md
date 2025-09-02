# BeauchBot - AI Assistant with Twilio Integration

A Python FastAPI service that provides an AI assistant capable of responding to text messages via Twilio webhooks and performing scheduled tasks.

## Features

- **Secure Twilio Webhooks**: Validates incoming requests with signature verification
- **AI Text Message Responses**: Automatically responds to SMS messages
- **Google Docs Integration**: Read Google Docs for system prompts and data
- **Contact Management**: Look up phone numbers from Google Docs
- **Scheduled Tasks**: Cron job support with time simulation for testing
- **Eastern Time**: Consistent EST/EDT timezone handling

## API Endpoints

- `GET /` - Redirects to API documentation
- `POST /message` - Twilio webhook endpoint (secured with signature validation)

## Setup

### Environment Variables

Create a `.env` file with:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
MY_PHONE_NUMBER=your_personal_phone_number

# Google (Base64 encoded service account JSON)
GOOGLE_SERVICE_ACCOUNT_B64=your_encoded_service_account

# System prompt (Google Doc ID)
SYSTEM_PROMPT_DOC_ID=your_system_prompt_document_id

# Attendance Sheets (for attendance tracking)
ATTENDANCE_SHEET_ID=your_attendance_google_sheets_document_id
```

### Using Docker (Recommended)

```shell
docker-compose up --build
```

The API will be available at http://localhost:8000

### Local Development

```shell
uv sync --no-editable
uv run uvicorn message_server:app --reload
```

## Twilio Setup

1. **Configure webhook URL** in [Twilio Console](https://console.twilio.com/):
   - Phone Numbers → Active numbers → Select your number
   - Messaging webhook: `https://your-domain.com/message` (POST)

2. **Local development** with ngrok:
   ```bash
   ngrok http 8000
   # Use: https://abc123.ngrok.io/message
   ```

3. **Security**: Webhook automatically validates Twilio signatures using your auth token.

## Scheduled Tasks

Run scheduled tasks using `scripts/ping_agent.py`:

```bash
# Normal execution (Eastern time)
python scripts/ping_agent.py

# Dry run (no text/SMS tools)
python scripts/ping_agent.py --dry-run

# Test with simulated time
python scripts/ping_agent.py --simulate-time "2024-01-15,09:00"
```

Add to crontab for automated execution:
```bash
# Run every hour
0 * * * * cd /path/to/beauchbot && python scripts/ping_agent.py >> /var/log/beauchbot_cron.log 2>&1
```

## Google Docs Configuration

### System Prompt Document

Create a Google Document with the agent's instructions and behavior:

1. Create a Google Doc with your system prompt
2. Share with your service account email (viewer access)
3. Get document ID from URL: `docs.google.com/document/d/DOCUMENT_ID/edit`
4. Set `SYSTEM_PROMPT_DOC_ID` environment variable

### Contact Management

BeauchBot can look up phone numbers from a Google Doc. Create a document with:
```
Name: Phone Number
John: +15551234567
Jane: +15559876543
```

## Available Tools

- **list_google_documents** - List accessible Google Docs
- **read_google_document** - Read specific Google Documents  
- **get_conversation_history** - Get SMS conversation history
- **text_me** - Send SMS to your personal number (MY_PHONE_NUMBER)
- **get_phone_numbers** - Look up contacts from Google Doc
- **get_current_time** - Get current Eastern time

## Example Usage

```
You: "Text me a reminder about the meeting"
BeauchBot: [sends SMS to your personal phone]

You: "What time is it?"
BeauchBot: "The current time is 2:30 PM EST."

You: "List my Google documents"
BeauchBot: "I found 5 documents: Meeting Notes, Project Plan, Budget..."

You: "Read the Meeting Notes document"
BeauchBot: "Here's the content from Meeting Notes: [document content]"
```

## Deployment

Configured for deployment on Render via `render.yaml`. Add environment variables to your Render dashboard and deploy.

## Development

```shell
# Add dependencies
uv add package-name

# Update dependencies  
uv sync --upgrade --no-editable

# Activate virtual environment
source .venv/bin/activate  # Unix/Mac
.venv\Scripts\activate     # Windows

# Or run commands directly with uv
uv run python script.py
```