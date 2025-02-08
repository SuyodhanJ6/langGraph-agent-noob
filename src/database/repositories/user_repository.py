from typing import Optional, Dict, Any
import json
from src.database.connection import DatabaseConnection
from src.utils.logger import logger

class UserRepository:
    def __init__(self):
        self.db = DatabaseConnection()
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure users table exists"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        metadata JSON,
                        INDEX idx_user_id (user_id),
                        INDEX idx_last_active (last_active)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                logger.info("Users table verified/created successfully")
                
        except Exception as e:
            logger.error(f"Error ensuring users table: {str(e)}")
            raise
    
    def get_or_create_user(self, user_id: str, metadata: dict = None) -> Dict[str, Any]:
        """Get existing user or create a new one"""
        try:
            with self.db.get_cursor(dictionary=True) as cursor:
                # Check if user exists
                cursor.execute("""
                    SELECT 
                        user_id,
                        created_at,
                        last_active,
                        metadata
                    FROM users 
                    WHERE user_id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    # Create new user
                    cursor.execute("""
                        INSERT INTO users (user_id, metadata)
                        VALUES (%s, %s)
                    """, (
                        user_id,
                        json.dumps(metadata) if metadata else None
                    ))
                    
                    # Get the created user
                    cursor.execute("""
                        SELECT 
                            user_id,
                            created_at,
                            last_active,
                            metadata
                        FROM users 
                        WHERE user_id = %s
                    """, (user_id,))
                    result = cursor.fetchone()
                
                if not result:
                    raise Exception(f"Failed to create or retrieve user {user_id}")
                
                return {
                    'user_id': result['user_id'],
                    'created_at': result['created_at'],
                    'last_active': result['last_active'],
                    'metadata': json.loads(result['metadata']) if result['metadata'] else None
                }
                
        except Exception as e:
            logger.error(f"Error managing user: {str(e)}")
            raise
    
    def update_last_active(self, user_id: str) -> bool:
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET last_active = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user_id,))
                return True
        except Exception as e:
            logger.error(f"Error updating user last active: {str(e)}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self.db.get_cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        user_id,
                        created_at,
                        last_active,
                        metadata
                    FROM users
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'user_id': result['user_id'],
                        'created_at': result['created_at'],
                        'last_active': result['last_active'],
                        'metadata': json.loads(result['metadata']) if result['metadata'] else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None 