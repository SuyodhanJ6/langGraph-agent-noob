from typing import Dict, Any, Optional, List
from datetime import datetime
from src.utils.logger import logger
from src.database.repositories.fraud_report import FraudReportRepository
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.chat_repository import ChatRepository, ChatMessage

class DatabaseService:
    def __init__(self):
        self.chat_repo = ChatRepository()
        self.user_repo = UserRepository()
        self.fraud_repo = FraudReportRepository()
    
    def save_message(
        self, 
        session_id: str, 
        user_id: str, 
        role: str, 
        content: str, 
        name: str = None, 
        metadata: dict = None
    ) -> bool:
        try:
            return self.chat_repo.save_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                agent_name=name,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise
    
    def get_session_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        try:
            messages = self.chat_repo.get_session_messages(session_id, limit)
            return [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'name': msg.name,
                    'created_at': msg.created_at,
                    'metadata': msg.metadata,
                    'message_id': msg.message_id,
                    'turn_number': msg.turn_number
                } for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error getting session messages: {str(e)}")
            return []
    
    def check_phone_number(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Check if a phone number has been reported"""
        try:
            return self.fraud_repo.check_number(phone_number)
        except Exception as e:
            logger.error(f"Error checking phone number: {str(e)}")
            return None
    
    def report_fraud(self, phone_number: str, description: str, reporter_ip: str) -> bool:
        """Report a fraudulent phone number"""
        try:
            return self.fraud_repo.report_fraud(phone_number, description, reporter_ip)
        except Exception as e:
            logger.error(f"Error reporting fraud: {str(e)}")
            return False
    
    def get_or_create_user(self, user_id: str, metadata: dict = None) -> Dict[str, Any]:
        """Get or create a user"""
        try:
            return self.user_repo.get_or_create_user(user_id, metadata)
        except Exception as e:
            logger.error(f"Error managing user: {str(e)}")
            raise 