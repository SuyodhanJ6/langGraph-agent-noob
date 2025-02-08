from src.database.connection import DatabaseConnection
from src.utils.logger import logger
import time

def wait_for_db():
    """Wait for database to be ready"""
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            db = DatabaseConnection()
            with db.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {i+1}/{max_retries}): {str(e)}")
            if i < max_retries - 1:
                time.sleep(retry_interval)
    
    raise Exception("Failed to connect to database after maximum retries")

if __name__ == "__main__":
    wait_for_db() 