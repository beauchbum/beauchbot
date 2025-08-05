# BeauchBot - AI Assistant with Twilio Integration

A Python [FastAPI](https://fastapi.tiangolo.com) service that provides an AI assistant (BeauchBot) capable of responding to text messages via Twilio webhooks and performing various tasks through MCP (Model Context Protocol) tools.

## Features

- **AI-Powered Text Message Responses**: BeauchBot automatically responds to incoming text messages
- **Dynamic System Prompts**: Agent behavior is controlled via Google Docs (required configuration)
- **Google Workspace Integration**: Read Google Docs, Sheets, and Calendar documents
- **Spreadsheet Analysis**: Access and analyze Google Sheets data with formatted output
- **Twilio Integration**: Send and receive SMS messages
- **MCP Tools**: Extensible tool system for various functionalities

## API Endpoints

- `GET /` - Health check endpoint
- `GET /agent?query=<message>` - Direct agent interaction for testing
- `POST /message` - Twilio webhook endpoint for incoming SMS messages

## Development Setup

### Using Docker (Recommended)

1. Install Docker and Docker Compose on your system
2. **Configure system prompt document** (see Dynamic System Prompt Configuration section)
3. Set required environment variables in `.env` file
4. Build and start the services:
   ```shell
   docker-compose up --build
   ```
5. The API will be available at http://localhost:8000
6. The MCP server will be available at http://localhost:8888

**Note**: BeauchBot requires a properly configured system prompt Google Document to function.

### Local Setup (Alternative)

1. Install Poetry (if you haven't already):
   ```shell
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```shell
   poetry install
   ```

3. Run the development server:
   ```shell
   poetry run uvicorn main:app --reload
   ```

## Twilio Webhook Setup

To enable BeauchBot to respond to incoming text messages:

1. **Configure your Twilio phone number webhook URL**:
   - In the [Twilio Console](https://console.twilio.com/), go to Phone Numbers > Manage > Active numbers
   - Select your Twilio phone number
   - In the Messaging section, set the webhook URL to: `https://your-domain.com/message`
   - Set the HTTP method to `POST`

2. **For local development with ngrok**:
   ```bash
   # Install ngrok and expose your local server
   ngrok http 8000
   
   # Use the ngrok URL in Twilio webhook configuration
   # Example: https://abc123.ngrok.io/message
   ```

3. **Environment variables required**:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   GOOGLE_SERVICE_ACCOUNT_B64=your_base64_encoded_service_account
   SYSTEM_PROMPT_DOC_ID=your_system_prompt_document_id  # Required for cron jobs
   ```

4. **Test the integration**:
   - Send a text message to your Twilio phone number
   - BeauchBot will process the message and respond intelligently

## Cron Job Setup

BeauchBot can run scheduled tasks via cron jobs using the `scripts/ping_agent.py` script.

### Setting up the Cron Job

1. **Prepare the system prompt**: Create a Google Doc with instructions for what the agent should do during scheduled execution (e.g., check calendar, send reminders, process tasks).

2. **Set the SYSTEM_PROMPT_DOC_ID**: Make sure your `.env` file includes the document ID:
   ```
   SYSTEM_PROMPT_DOC_ID=your_google_doc_id_here
   ```

3. **Test the script**:
   ```bash
   # Test without execution (dry run)
   python scripts/ping_agent.py --dry-run
   
   # Test with execution
   python scripts/ping_agent.py
   ```

4. **Add to crontab**:
   ```bash
   # Edit crontab
   crontab -e
   
   # Add entry to run every hour (adjust path as needed)
   0 * * * * cd /path/to/beauchbot && python scripts/ping_agent.py >> /var/log/beauchbot_cron.log 2>&1
   ```

### Cron Job Features

- **Google Doc System Prompt**: Agent reads instructions from a Google Doc, allowing you to update behavior without code changes
- **Logging**: Comprehensive logging for monitoring cron job execution
- **Error Handling**: Robust error handling with proper exit codes
- **Dry Run Mode**: Test configuration without executing actions
   - Check the application logs to see the processing details

## Dynamic System Prompt Configuration

BeauchBot requires a Google Document as its system prompt, allowing you to easily modify the agent's behavior without code changes. The system will not function without a properly configured system prompt document.

### Setup System Prompt Document

1. **Create a Google Document** containing your desired system prompt
2. **Share the document** with your service account email (with viewer permissions)
3. **Get the document ID** from the URL: `https://docs.google.com/document/d/DOCUMENT_ID/edit`
4. **Set the environment variable**:
   ```bash
   export SYSTEM_PROMPT_DOC_ID="your_document_id_here"
   ```

### System Prompt Tips

- Define BeauchBot's personality and communication style
- Specify available tools and their usage guidelines
- Include any specific instructions for handling different types of requests
- The system prompt is fetched fresh each time an agent is created

### Example System Prompt Structure

```
You are BeauchBot, a helpful AI assistant with the following capabilities:

PERSONALITY:
- Friendly and professional tone
- Concise but thorough responses
- Proactive in offering assistance

AVAILABLE TOOLS:
- send_text: Send SMS messages to contacts
- get_contact: Look up contact information
- read_calendar: Access calendar information
- list_google_documents: List accessible Google Docs
- read_google_document: Read specific documents
- [etc...]

GUIDELINES:
- Always verify contact names before sending messages
- Ask for clarification when requests are ambiguous
- Provide summaries for long documents
```

### Error Handling

If the system prompt document cannot be accessed, BeauchBot will fail to start and log detailed error messages. This ensures that the agent always operates with the intended configuration.

## What BeauchBot Can Do

When you send a text message to your Twilio number, BeauchBot can:

### Basic Interactions
- Respond to greetings and general conversation
- Answer questions about current time and date
- Provide helpful information and assistance



### Google Docs & Sheets Integration
- List all accessible documents: "What Google Docs do I have access to?"
- List all accessible spreadsheets: "Show me my Google Sheets"
- Read any document by ID: "Read document [ID] for me"
- Read spreadsheet data: "Show me the Budget spreadsheet"
- Read specific sheet tabs: "Read the 'Q1 Data' tab from my budget sheet"
- Read your calendar: "What's on my calendar today?"
- Check upcoming events and appointments
- Provide calendar summaries

### Message Examples
```
You: "Hi BeauchBot!"
BeauchBot: "Hello! I'm BeauchBot, your AI assistant. How can I help you today?"

You: "What time is it?"
BeauchBot: "The current time is 2:30 PM EST."

You: "Send Ryan a message saying the meeting is at 3pm"
BeauchBot: "I'll send that message to Ryan now." [sends text to Ryan's number]

You: "What's on my calendar?"
BeauchBot: "Let me check your calendar..." [reads and summarizes calendar]

You: "What Google documents do I have access to?"
BeauchBot: "I found 12 documents. Here are the most recent ones: Meeting Notes (Jan 15), Project Plan (Jan 10), Budget 2024 (Jan 5)..."

You: "Show me my Google Sheets"
BeauchBot: "I found 8 spreadsheets: Budget 2024 (Jan 12), Sales Data (Jan 8), Team Contacts (Dec 20)..."

You: "Read the Budget 2024 spreadsheet"
BeauchBot: "Spreadsheet: Budget 2024
Sheet: Q1 Budget

Data (15 rows):
Category    | Jan    | Feb    | Mar    | Total
-----------|--------|--------|--------|--------
Marketing  | 5000   | 5500   | 6000   | 16500
Sales      | 12000  | 13000  | 14000  | 39000
..."

You: "Read the Meeting Notes document for me"
BeauchBot: "Here's the content from Meeting Notes: [document content]"
```

## Deployment on Render

This project is configured for deployment on Render.

1. Create a new Web Service on Render
2. Link your repository
3. Add all required environment variables in the Render dashboard
4. The build and start commands are already configured in `render.yaml`
5. Click "Create Web Service"
6. Update your Twilio webhook URL to point to your Render deployment

Or simply click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## Managing Dependencies

To add new dependencies:
```shell
poetry add package-name
```

To update dependencies:
```shell
poetry update
```

To activate the virtual environment:
```shell
poetry shell
```

## Thanks

Thanks to [Harish](https://harishgarg.com) for the [inspiration to create a FastAPI quickstart for Render](https://twitter.com/harishkgarg/status/1435084018677010434) and for some sample code!