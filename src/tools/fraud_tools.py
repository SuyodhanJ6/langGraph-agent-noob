from langchain.tools import tool
from src.services.database_service import DatabaseService

class FraudTools:
    def __init__(self):
        self.db = DatabaseService()

    @tool
    def check_phone_number(self, phone_number: str) -> str:
        """Check if a phone number is reported as scam. Input should be a string containing just the phone number."""
        try:
            # Clean the phone number
            phone_number = phone_number.strip().replace(" ", "").replace("-", "").replace("+", "")
            result = self.db.check_number(phone_number)
            
            if result and isinstance(result, dict) and result.get('report_count', 0) > 0:
                return f"Fraud reports: {result['report_count']}"
            return "No reports found"
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    @tool
    def register_fraud_report(self, phone_number: str, description: str) -> str:
        """Register a phone number as potentially fraudulent. 
        Input should be a phone number and a description of the fraudulent activity."""
        try:
            # Clean the phone number
            phone_number = phone_number.strip().replace(" ", "").replace("-", "").replace("+", "")
            success = self.db.report_fraud(phone_number, description, "127.0.0.1")
            if success:
                return "Report successfully registered. Thank you for helping protect others."
            return "Failed to register report"
        except Exception as e:
            raise Exception(f"Error registering report: {str(e)}") 