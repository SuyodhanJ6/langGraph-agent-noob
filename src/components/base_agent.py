from abc import ABC, abstractmethod
from langchain_core.messages import AIMessage, HumanMessage
from src.utils.logger import logger
from src.constants.routes import AgentRoutes
from typing import Dict, Any

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def create_response(self, state: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create a response that includes both messages and next step"""
        messages = state.get("messages", []) + [
            AIMessage(content=content, name=self.name)
        ]
        return {
            "messages": messages,
            "next": AgentRoutes.SUPERVISOR.value
        }
    
    def extract_content(self, response: Any) -> str:
        try:
            if isinstance(response, dict):
                if 'output' in response:
                    return response['output']
                elif 'messages' in response and response['messages']:
                    return response['messages'][-1].content
                elif 'tool_calls' in response.get('additional_kwargs', {}):
                    # Handle tool call responses
                    tool_calls = response['additional_kwargs']['tool_calls']
                    return f"Tool call: {tool_calls}"
            return str(response)
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return str(response) 