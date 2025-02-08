from src.services.agent_service import AgentService
from src.utils.logger import logger
from typing import Dict, Any

class ChatService:
    def __init__(self):
        self.agent_service = AgentService()
    
    async def process_chat(self, message: str, session_id: str, user_id: str) -> Dict[str, Any]:
        try:
            response = await self.agent_service.process_message(
                message=message,
                session_id=session_id,
                user_id=user_id
            )
            return response
        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            raise 