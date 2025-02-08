from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict] = None
    message_id: Optional[str] = None
    turn_number: Optional[int] = None

@dataclass
class ChatSession:
    session_id: str
    user_id: str
    status: str = 'active'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    metadata: Optional[Dict] = None 