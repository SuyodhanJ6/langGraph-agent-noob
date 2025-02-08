from src.components.base_agent import BaseAgent
from src.utils.logger import logger
from src.constants.routes import AgentRoutes
from src.prompts.checker_prompts import CheckerPrompts
from typing import Dict, Any
import json
import re
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class CheckerAgent(BaseAgent):
    def __init__(self, agent):
        super().__init__("checker")
        self.agent = agent
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"{self.name} node processing...")
            last_message = state["messages"][-1]
            
            if isinstance(last_message, HumanMessage):
                # First, try to understand and extract phone number
                response = self.agent.invoke({
                    "messages": [
                        SystemMessage(content=CheckerPrompts.SYSTEM),
                        HumanMessage(content=last_message.content)
                    ]
                })
                
                logger.info(f"Initial response: {response}")
                
                # If we got a valid number, format it
                phone_number = self._extract_phone_number(last_message.content)
                if phone_number:
                    return self.create_response(
                        state,
                        f"I found the phone number {phone_number}. Let me check it for any fraud reports."
                    )
                
                # If we need clarification
                return self.create_response(
                    state,
                    "I need a valid phone number to check. Please provide the number "
                    "in the format: +1-XXX-XXX-XXXX (for example: +1-555-123-4567)"
                )
            
            # For non-human messages, just pass through
            return self.create_response(
                state, 
                "I can help you check a phone number for fraud reports. "
                "Please provide the number you'd like to check."
            )
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return self.create_response(
                state,
                "I apologize, but I encountered an error. Please provide a phone number "
                "in the format: +1-XXX-XXX-XXXX (for example: +1-555-123-4567)"
            )

    def _extract_phone_number(self, content: str) -> str:
        """Extract phone number from content"""
        try:
            # Try various phone number formats
            patterns = [
                r'\+1-\d{3}-\d{3}-\d{4}',  # +1-XXX-XXX-XXXX
                r'\d{10}',                  # XXXXXXXXXX
                r'\d{3}-\d{3}-\d{4}',      # XXX-XXX-XXXX
                r'\(\d{3}\)\s*\d{3}-\d{4}' # (XXX) XXX-XXXX
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    number = match.group()
                    # Convert to standard format
                    digits = re.sub(r'\D', '', number)
                    if len(digits) == 10:
                        return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
                    elif len(digits) == 11 and digits.startswith('1'):
                        return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting phone number: {e}")
            return None

    def _format_response(self, phone_number: str) -> str:
        """Format a user-friendly response"""
        if not phone_number:
            return (
                "I need a valid phone number to check. Please provide the number "
                "in the format: +1-XXX-XXX-XXXX (for example: +1-555-123-4567)"
            )
        
        # Format number in standard format
        try:
            digits = re.sub(r'\D', '', phone_number)
            if len(digits) == 10:
                formatted = f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits.startswith('1'):
                formatted = f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            else:
                return (
                    f"The number {phone_number} doesn't appear to be a valid US phone number. "
                    "Please provide a number in the format: +1-XXX-XXX-XXXX"
                )
            
            return (
                f"I'll check the number {formatted} for any reported fraud. "
                "Please confirm this is the correct number."
            )
            
        except Exception as e:
            logger.error(f"Error formatting phone number: {e}")
            return (
                "I had trouble understanding that number format. "
                "Please provide the number in the format: +1-XXX-XXX-XXXX"
            ) 