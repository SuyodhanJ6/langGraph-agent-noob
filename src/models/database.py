from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class FraudReport(BaseModel):
    id: Optional[int] = None
    phone_number: str
    is_fraud: bool = False
    report_count: int = 0
    first_reported_at: datetime
    last_updated_at: datetime
    description: str
    reporter_ip: str

class UserReport(BaseModel):
    id: Optional[int] = None
    user_name: Optional[str]
    email: Optional[str]
    phone_number: str
    created_at: datetime

class ConversationHistory(BaseModel):
    id: Optional[int] = None
    session_id: str
    user_id: str
    role: str
    content: str
    name: Optional[str]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] 