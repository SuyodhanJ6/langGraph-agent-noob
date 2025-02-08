from src.database.connection import DatabaseConnection
from src.utils.logger import logger

def init_database():
    try:
        db = DatabaseConnection()
        with db.get_cursor() as cursor:
            # Create users table
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

            # Create message analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_analytics (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    message_id VARCHAR(100) NOT NULL UNIQUE,
                    session_id VARCHAR(100) NOT NULL,
                    processing_time FLOAT,
                    token_count INT,
                    completion_tokens INT,
                    prompt_tokens INT,
                    model_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    INDEX idx_message_stats (message_id),
                    INDEX idx_session_stats (session_id),
                    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            db.connection.commit()
            logger.info("Production database schema created successfully")
            
    except Exception as e:
        logger.error(f"Error creating database schema: {e}")
        raise 