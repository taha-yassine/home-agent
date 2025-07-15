from pydantic import BaseModel
from typing import Any, Dict, List
from datetime import datetime

class ConversationRequest(BaseModel):
    """Model for conversation request."""
    text: str
    conversation_id: str
    language: str
    home_state: Dict[str, Any]

class ConversationResponse(BaseModel):
    """Model for conversation response."""
    response: str


class Conversation(BaseModel):
    """Model for a single conversation."""

    id: str
    started_at: datetime
    instruction: str


class ConversationList(BaseModel):
    """Model for a list of conversations."""

    conversations: List[Conversation] 