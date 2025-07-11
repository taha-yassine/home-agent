from pydantic import BaseModel
from typing import Any, Dict

class ConversationRequest(BaseModel):
    """Model for conversation request."""
    text: str
    conversation_id: str
    language: str
    home_state: Dict[str, Any]

class ConversationResponse(BaseModel):
    """Model for conversation response."""
    response: str 