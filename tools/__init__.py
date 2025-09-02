"""
Tools package for BeauchBot.

Organized into logical modules:
- google_docs: Google Docs and Drive integration
- twilio: SMS and Group MMS messaging
- system: Basic system utilities
"""

# Import all tools from modules
from .google_docs import (
    list_google_documents,
    read_google_document, 
    get_phone_numbers,
    write_attendance
)

from .twilio import (
    send_text,
    get_conversation_history,
    text_me,
    send_text_dry
)

from .system import (
    get_current_time
)

# Tools are now functions decorated with @function_tool, no need to instantiate
