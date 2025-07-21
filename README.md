# BeauchBot - AI Assistant with Twilio Integration

A Python [FastAPI](https://fastapi.tiangolo.com) service that provides an AI assistant (BeauchBot) capable of responding to text messages via Twilio webhooks and performing various tasks through MCP (Model Context Protocol) tools.

## Features

- **AI-Powered Text Message Responses**: BeauchBot automatically responds to incoming text messages
- **Contact Management**: Look up contacts by name for easy messaging
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
2. Build and start the services:
   ```shell
   docker-compose up --build
   ```
3. The API will be available at http://localhost:8000
4. The MCP server will be available at http://localhost:8888

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
   ```

4. **Test the integration**:
   - Send a text message to your Twilio phone number
   - BeauchBot will process the message and respond intelligently
   - Check the application logs to see the processing details

## What BeauchBot Can Do

When you send a text message to your Twilio number, BeauchBot can:

### Basic Interactions
- Respond to greetings and general conversation
- Answer questions about current time and date
- Provide helpful information and assistance

### Contact Management
- Look up contacts by name: "What's John's number?"
- Send messages to contacts: "Send John a message saying hello"
- List all available contacts

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