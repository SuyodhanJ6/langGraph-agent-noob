from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
from src.database.connection import DatabaseConnection
from src.utils.logger import logger
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

class ChatRepository:
    def __init__(self):
        self.db = DatabaseConnection()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure chat tables exist"""
        try:
            with self.db.get_cursor() as cursor:
                # Create chat sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(100) NOT NULL UNIQUE,
                        user_id VARCHAR(100) NOT NULL,
                        status ENUM('active', 'inactive', 'completed') DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSON,
                        INDEX idx_session_lookup (session_id, status),
                        INDEX idx_user_sessions (user_id, status),
                        INDEX idx_last_message (last_message_at),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

                # Create chat messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        message_id VARCHAR(100) NOT NULL UNIQUE,
                        session_id VARCHAR(100) NOT NULL,
                        user_id VARCHAR(100) NOT NULL,
                        role ENUM('user', 'assistant', 'system') NOT NULL,
                        content TEXT NOT NULL,
                        agent_name VARCHAR(50),
                        turn_number INT NOT NULL,
                        parent_message_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSON,
                        embedding_vector BLOB,
                        
                        INDEX idx_message_lookup (message_id),
                        INDEX idx_session_turn (session_id, turn_number),
                        INDEX idx_user_messages (user_id, created_at),
                        INDEX idx_parent_child (parent_message_id),
                        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                self.db.connection.commit()
        except Exception as e:
            logger.error(f"Error ensuring chat tables: {e}")
            raise

    def get_or_create_session(self, session_id: str, user_id: str) -> str:
        try:
            with self.db.get_cursor() as cursor:
                # Check if session exists
                cursor.execute("""
                    SELECT session_id FROM chat_sessions 
                    WHERE session_id = %s AND status = 'active'
                """, (session_id,))
                
                result = cursor.fetchone()
                if not result:
                    # Create new session
                    cursor.execute("""
                        INSERT INTO chat_sessions (session_id, user_id)
                        VALUES (%s, %s)
                    """, (session_id, user_id))
                    self.db.connection.commit()
                return session_id
        except Exception as e:
            logger.error(f"Error managing session: {e}")
            raise
    
    def save_message(
        self, 
        session_id: str, 
        user_id: str, 
        role: str, 
        content: str, 
        agent_name: str = None, 
        metadata: dict = None,
        parent_message_id: str = None
    ) -> bool:
        try:
            with self.db.get_cursor() as cursor:
                # Get next turn number
                cursor.execute("""
                    SELECT COALESCE(MAX(turn_number), 0) + 1
                    FROM chat_messages
                    WHERE session_id = %s
                """, (session_id,))
                turn_number = cursor.fetchone()[0]

                # Generate unique message ID
                message_id = str(uuid.uuid4())

                # Insert message
                cursor.execute("""
                    INSERT INTO chat_messages (
                        message_id, session_id, user_id, role, content,
                        agent_name, turn_number, parent_message_id, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    message_id, session_id, user_id, role, content,
                    agent_name, turn_number, parent_message_id,
                    json.dumps(metadata) if metadata else None
                ))

                # Update session last_message_at
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET last_message_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (session_id,))

                self.db.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise
    
    def get_session_messages(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get active conversation history for a session"""
        try:
            with self.db.get_cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        message_id,
                        role,
                        content,
                        agent_name as name,
                        turn_number,
                        created_at,
                        metadata
                    FROM chat_messages 
                    WHERE session_id = %s 
                    ORDER BY turn_number ASC
                    LIMIT %s
                """, (session_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append(ChatMessage(
                        role=row['role'],
                        content=row['content'],
                        name=row['name'],
                        created_at=row['created_at'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None,
                        message_id=row['message_id'],
                        turn_number=row['turn_number']
                    ))
                return messages
                
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return [] 