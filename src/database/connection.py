import mysql.connector
from mysql.connector import Error
from src.core.database import get_db_settings
from src.utils.logger import logger
import time
from contextlib import contextmanager

class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.settings = get_db_settings()
            self.connection = None
            self.initialized = True
            self.connect_and_setup()
    
    def connect_without_database(self):
        try:
            return mysql.connector.connect(
                host=self.settings.DB_HOST,
                port=self.settings.DB_PORT,
                user=self.settings.DB_USER,
                password=self.settings.DB_PASSWORD
            )
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise
    
    def create_database(self):
        try:
            conn = self.connect_without_database()
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.settings.DB_NAME}")
            cursor.close()
            conn.close()
            logger.info(f"Database {self.settings.DB_NAME} created successfully")
        except Error as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def connect_and_setup(self):
        max_retries = 3
        current_try = 0
        
        while current_try < max_retries:
            try:
                self.create_database()
                self.connection = mysql.connector.connect(
                    host=self.settings.DB_HOST,
                    port=self.settings.DB_PORT,
                    user=self.settings.DB_USER,
                    password=self.settings.DB_PASSWORD,
                    database=self.settings.DB_NAME
                )
                logger.info("Database connection successful")
                self.setup_tables()
                break
            except Error as err:
                current_try += 1
                logger.error(f"Attempt {current_try} failed: {err}")
                if current_try < max_retries:
                    time.sleep(2)
                else:
                    raise Exception(f"Failed to connect after {max_retries} attempts")
    
    @contextmanager
    def get_cursor(self, dictionary=False):
        cursor = self.connection.cursor(dictionary=dictionary)
        try:
            yield cursor
        finally:
            cursor.close()
    
    def setup_tables(self):
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
            
            # Create other tables...
            # Add your other table creation SQL here
            
            self.connection.commit()
            logger.info("Database tables created successfully") 