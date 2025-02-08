from typing import Optional, Dict, Any
from src.database.connection import DatabaseConnection
from src.models.database import FraudReport
from src.utils.logger import logger

class FraudReportRepository:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def check_number(self, phone_number: str) -> Optional[Dict[str, Any]]:
        try:
            with self.db.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM fraud_reports WHERE phone_number = %s",
                    (phone_number,)
                )
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error checking number: {e}")
            raise
    
    def report_fraud(self, phone_number: str, description: str, reporter_ip: str) -> bool:
        try:
            with self.db.get_cursor() as cursor:
                existing = self.check_number(phone_number)
                
                if existing:
                    cursor.execute("""
                        UPDATE fraud_reports 
                        SET is_fraud = TRUE, 
                            report_count = report_count + 1,
                            description = CONCAT(description, '\n', %s)
                        WHERE phone_number = %s
                    """, (description, phone_number))
                else:
                    cursor.execute("""
                        INSERT INTO fraud_reports 
                        (phone_number, is_fraud, report_count, description, reporter_ip)
                        VALUES (%s, TRUE, 1, %s, %s)
                    """, (phone_number, description, reporter_ip))
                
                self.db.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error reporting fraud: {e}")
            raise 