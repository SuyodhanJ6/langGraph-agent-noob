from src.components.base_agent import BaseAgent
from src.utils.logger import logger
from typing import Dict, Any

class ReporterAgent(BaseAgent):
    def __init__(self, agent):
        super().__init__("reporter")
        self.agent = agent
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"{self.name} node processing...")
            response = self.agent.invoke(state)
            logger.info(f"{self.name} response: {response}")
            
            content = self.extract_content(response)
            return self.create_response(state, content)
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return self.create_response(state, f"Error: {str(e)}") 