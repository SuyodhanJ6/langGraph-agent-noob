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
                self.db.connection.commit()
        except Exception as e:
            logger.error(f"Error ensuring users table: {e}")
            raise
    
    def get_or_create_user(self, user_id: str, metadata: dict = None) -> bool:
        try:
            with self.db.get_cursor() as cursor:
                # Try to insert new user
                cursor.execute("""
                    INSERT IGNORE INTO users (user_id, metadata)
                    VALUES (%s, %s)
                """, (
                    user_id,
                    json.dumps(metadata) if metadata else None
                ))
                self.db.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error in user operation: {e}")
            raise 