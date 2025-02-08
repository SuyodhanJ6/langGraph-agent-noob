from typing import List, Dict, Any
import json
from src.database.connection import DatabaseConnection
from src.utils.logger import logger

class ConversationRepository:
    def __init__(self):
        self.db = DatabaseConnection()
    
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
            with self.db.get_cursor() as cursor:
                # Get the next conversation turn (handle case where column might not exist)
                try:
                    cursor.execute("""
                        SELECT COALESCE(MAX(conversation_turn), 0) + 1
                        FROM conversation_history
                        WHERE session_id = %s
                    """, (session_id,))
                    next_turn = cursor.fetchone()[0]
                except Exception:
                    next_turn = 1  # Default if column doesn't exist yet

                # Insert new message
                cursor.execute("""
                    INSERT INTO conversation_history 
                    (session_id, user_id, role, content, name, metadata, conversation_turn)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id, user_id, role, content, name,
                    json.dumps(metadata) if metadata else None,
                    next_turn
                ))
                self.db.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            # Try without conversation_turn if it fails
            try:
                cursor.execute("""
                    INSERT INTO conversation_history 
                    (session_id, user_id, role, content, name, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    session_id, user_id, role, content, name,
                    json.dumps(metadata) if metadata else None
                ))
                self.db.connection.commit()
                return True
            except Exception as e2:
                logger.error(f"Error in fallback save: {e2}")
                raise
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active conversation history for a session"""
        try:
            with self.db.get_cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        role,
                        content,
                        name,
                        timestamp as created_at,
                        conversation_turn,
                        metadata
                    FROM conversation_history 
                    WHERE session_id = %s 
                        AND is_active = TRUE
                    ORDER BY conversation_turn ASC
                    LIMIT %s
                """, (session_id, limit))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def mark_session_inactive(self, session_id: str) -> bool:
        """Mark a session as inactive after long period of inactivity"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE conversation_history
                    SET is_active = FALSE
                    WHERE session_id = %s
                """, (session_id,))
                self.db.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking session inactive: {e}")
            return False 