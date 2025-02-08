from typing import List, Optional
from pydantic import BaseModel

class AgentResponse(BaseModel):
    """Response model for agent messages"""
    content: str
    name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello! I'm here to help you check or report fraudulent phone numbers.",
                "name": "greeter"
            }
        }

class AgentState(BaseModel):
    """Internal state model for agent processing"""
    messages: List[dict]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    next: Optional[str] = None 