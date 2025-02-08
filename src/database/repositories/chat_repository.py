from typing import List, Dict, Any, Optional
import json
import uuid
from src.database.connection import DatabaseConnection
from src.utils.logger import logger
from src.models.chat import ChatMessage, ChatSession
from src.database.repositories.user_repository import UserRepository

class ChatRepository:
    def __init__(self):
        self.db = DatabaseConnection()
        self.user_repo = UserRepository()
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

                # Create messages table
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
                
                logger.info("Chat tables verified/created successfully")
                
        except Exception as e:
            logger.error(f"Error ensuring chat tables: {str(e)}")
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
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    def get_or_create_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get existing session or create a new one"""
        try:
            # First ensure user exists
            self.user_repo.get_or_create_user(user_id)
            
            with self.db.get_cursor(dictionary=True) as cursor:
                # Check if session exists
                cursor.execute("""
                    SELECT 
                        session_id,
                        user_id,
                        status,
                        created_at,
                        updated_at,
                        last_message_at,
                        metadata
                    FROM chat_sessions 
                    WHERE session_id = %s AND status = 'active'
                """, (session_id,))
                
                result = cursor.fetchone()
                if not result:
                    # Create new session
                    cursor.execute("""
                        INSERT INTO chat_sessions 
                        (session_id, user_id, status, metadata) 
                        VALUES (%s, %s, 'active', NULL)
                    """, (session_id, user_id))
                    
                    # Get the created session
                    cursor.execute("""
                        SELECT 
                            session_id,
                            user_id,
                            status,
                            created_at,
                            updated_at,
                            last_message_at,
                            metadata
                        FROM chat_sessions 
                        WHERE session_id = %s
                    """, (session_id,))
                    result = cursor.fetchone()
                
                if not result:
                    raise Exception(f"Failed to create or retrieve session {session_id}")
                
                return {
                    'session_id': result['session_id'],
                    'user_id': result['user_id'],
                    'status': result['status'],
                    'created_at': result['created_at'],
                    'updated_at': result['updated_at'],
                    'last_message_at': result['last_message_at'],
                    'metadata': json.loads(result['metadata']) if result['metadata'] else None
                }
                
        except Exception as e:
            logger.error(f"Error managing session: {str(e)}")
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
            # First ensure session exists
            session = self.get_or_create_session(session_id, user_id)
            
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

                return True
                
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise 