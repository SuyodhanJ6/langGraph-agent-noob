import mysql.connector
from mysql.connector import Error, pooling
from src.core.config import get_settings
from src.utils.logger import logger
import time
from contextlib import contextmanager

class DatabaseConnection:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.settings = get_settings()
            self._setup_connection_pool()
            self.initialized = True
    
    def _setup_connection_pool(self):
        """Setup connection pool with proper error handling"""
        try:
            if not self._pool:
                # First try to connect without database to create it if needed
                self.create_database()
                
                pool_config = {
                    "pool_name": "mypool",
                    "pool_size": self.settings.DB_POOL_SIZE,
                    "host": self.settings.DB_HOST,
                    "port": int(self.settings.DB_PORT),
                    "user": self.settings.DB_USER,
                    "password": self.settings.DB_PASSWORD,
                    "database": self.settings.DB_NAME,
                    "connect_timeout": self.settings.DB_TIMEOUT,
                    "auth_plugin": 'mysql_native_password'
                }
                
                # Create the connection pool
                self._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
                logger.info("Database connection pool created successfully")
                
                # Initialize tables
                self.setup_tables()
        
        except Error as e:
            logger.error(f"Error creating connection pool: {str(e)}")
            if e.errno == 1045:  # Access denied error
                logger.error("Authentication failed. Please check your MySQL credentials.")
            elif e.errno == 2003:  # Can't connect to MySQL server
                logger.error("Cannot connect to MySQL server. Please check if MySQL is running.")
            raise Exception(f"Database connection failed: {str(e)}")
    
    def create_database(self):
        """Create database if it doesn't exist"""
        conn = None
        cursor = None
        try:
            # Try to connect without database first
            conn = mysql.connector.connect(
                host=self.settings.DB_HOST,
                port=int(self.settings.DB_PORT),
                user=self.settings.DB_USER,
                password=self.settings.DB_PASSWORD,
                auth_plugin='mysql_native_password'
            )
            
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.settings.DB_NAME}")
            cursor.execute(f"USE {self.settings.DB_NAME}")
            conn.commit()
            
            logger.info(f"Database {self.settings.DB_NAME} created/verified successfully")
            
        except Error as e:
            logger.error(f"Error creating database: {str(e)}")
            if e.errno == 1045:
                raise Exception(
                    "MySQL authentication failed. Please check your credentials in .env file"
                )
            raise Exception(f"Failed to create database: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with proper error handling"""
        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        except Error as e:
            logger.error(f"Error getting connection from pool: {str(e)}")
            raise Exception(f"Database connection error: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Error:
                    pass
    
    @contextmanager
    def get_cursor(self, dictionary=False):
        """Get a cursor using a pooled connection"""
        conn = None
        cursor = None
        try:
            conn = self._pool.get_connection()
            cursor = conn.cursor(dictionary=dictionary)
            yield cursor
            conn.commit()  # Commit after successful execution
        except Error as e:
            if conn:
                conn.rollback()  # Rollback on error
            logger.error(f"Database cursor error: {str(e)}")
            raise Exception(f"Database operation failed: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def setup_tables(self):
        """Setup database tables with error handling"""
        try:
            with self.get_cursor() as cursor:
                # Create fraud_reports table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fraud_reports (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        phone_number VARCHAR(20),
                        is_fraud BOOLEAN DEFAULT FALSE,
                        report_count INT DEFAULT 0,
                        first_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        description TEXT,
                        reporter_ip VARCHAR(45),
                        INDEX idx_phone (phone_number)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        metadata JSON,
                        INDEX idx_user_id (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create chat_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(100) NOT NULL UNIQUE,
                        user_id VARCHAR(100) NOT NULL,
                        status ENUM('active', 'inactive', 'completed') DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        metadata JSON,
                        INDEX idx_session_lookup (session_id, status),
                        INDEX idx_user_sessions (user_id, status),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create chat_messages table
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSON,
                        INDEX idx_session_turn (session_id, turn_number),
                        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Error setting up tables: {str(e)}")
            raise Exception(f"Failed to setup database tables: {str(e)}") 