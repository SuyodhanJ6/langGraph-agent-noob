from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from src.services.agent_service import AgentService
from src.models.agents import AgentResponse
from src.core.config import settings
from src.utils.logger import logger
import time

router = APIRouter()

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    content: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hi, I want to check a phone number",
                "session_id": "session_123",
                "user_id": "user_456"
            }
        }

@router.post("/chat", response_model=AgentResponse, 
            summary="Process a chat message",
            description="Send a message to the fraud detection system")
async def chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(lambda: AgentService())
):
    """
    Process a chat message and return the agent's response.
    
    Args:
        request: ChatRequest containing the message content and optional session/user IDs
        
    Returns:
        AgentResponse containing the assistant's response
        
    Raises:
        HTTPException: If there's an error processing the message
    """
    try:
        # Generate default IDs if not provided
        session_id = request.session_id or f"session_{int(time.time())}"
        user_id = request.user_id or f"user_{int(time.time())}"
        
        response = await agent_service.process_message(
            message=request.content,
            session_id=session_id,
            user_id=user_id
        )
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@router.get("/health", 
           summary="Health check endpoint",
           description="Check if the API is running")
async def health_check():
    """Return the API health status and version"""
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "model": settings.GROQ_MODEL
    } 