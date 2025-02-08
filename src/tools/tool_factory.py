from typing import List
from langchain.tools import BaseTool
from src.tools.fraud_tools import FraudTools

class ToolFactory:
    @staticmethod
    def get_checker_tools() -> List[BaseTool]:
        fraud_tools = FraudTools()
        return [fraud_tools.check_phone_number]
    
    @staticmethod
    def get_reporter_tools() -> List[BaseTool]:
        fraud_tools = FraudTools()
        return [fraud_tools.register_fraud_report]
    
    @staticmethod
    def get_all_tools() -> List[BaseTool]:
        fraud_tools = FraudTools()
        return [
            fraud_tools.check_phone_number,
            fraud_tools.register_fraud_report
        ] 