"""
Tools package for BeauchBot.

Organized into logical modules:
- google_docs: Google Docs and Drive integration
- twilio: SMS and Group MMS messaging
- system: Basic system utilities
"""

# Import all tools from modules
from .google_docs import (
    ListGoogleDocumentsTool,
    ReadGoogleDocumentTool, 
    GetPhoneNumbersTool
)

from .twilio import (
    SendTextTool,
    GetConversationHistoryTool,
)

from .system import (
    GetCurrentTimeTool
)

# Create tool instances for use in agents
list_google_documents = ListGoogleDocumentsTool()
read_google_document = ReadGoogleDocumentTool()
send_text = SendTextTool()
get_conversation_history = GetConversationHistoryTool()
get_phone_numbers = GetPhoneNumbersTool()
get_current_time = GetCurrentTimeTool()
