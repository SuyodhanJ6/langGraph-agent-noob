from src.components.base_agent import BaseAgent
from src.utils.logger import logger
from src.constants.routes import AgentRoutes
from src.prompts.greeter_prompts import GreeterPrompts
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class GreeterAgent(BaseAgent):
    def __init__(self, agent):
        super().__init__("greeter")
        self.agent = agent
    
    def _find_user_name(self, messages: list) -> str:
        """Extract user's name from conversation history"""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                content = msg.content.lower()
                if "my name is" in content or "i am" in content:
                    # Extract name after "my name is" or "i am"
                    name_parts = content.split("my name is" if "my name is" in content else "i am")
                    if len(name_parts) > 1:
                        return name_parts[1].strip().title()
        return None

    def _get_context_aware_response(self, state: Dict[str, Any], current_message: str) -> str:
        """Generate context-aware response based on conversation history"""
        messages = state.get("messages", [])
        
        if "what is my name" in current_message.lower():
            user_name = self._find_user_name(messages)
            if user_name:
                return f"Based on our conversation, your name is {user_name}. How can I help you with phone fraud detection today?"
        
        # Handle name introduction
        if "my name is" in current_message.lower():
            name = current_message.lower().split("my name is")[1].strip().title()
            return (
                f"Hello {name}, welcome to our phone fraud detection service. "
                "I'm here to help you identify and report suspicious phone numbers.\n\n"
                "This service allows you to check if a phone number is associated with any known scams "
                "or fraudulent activities. You can also report any numbers you suspect of being involved "
                "in phone fraud.\n\n"
                "Would you like to check a phone number for potential fraud or report a number you "
                "suspect of being involved in a scam?"
            )
        
        return None

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"{self.name} node processing...")
            last_message = state["messages"][-1]
            history = state["messages"][:-1]
            
            if isinstance(last_message, HumanMessage):
                # Format conversation history
                history_str = "\n".join([
                    f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
                    for m in history
                ])
                
                # Determine the appropriate prompt based on message content
                if "my name is" in last_message.content.lower():
                    prompt = GreeterPrompts.INTRODUCTION.format(
                        message=last_message.content
                    )
                elif any(q in last_message.content.lower() for q in ["what is my name", "who am i", "remember me"]):
                    prompt = GreeterPrompts.MEMORY_QUERY.format(
                        conversation_history=history_str,
                        question=last_message.content
                    )
                else:
                    prompt = GreeterPrompts.CONTEXT_ANALYSIS.format(
                        conversation_history=history_str,
                        current_message=last_message.content
                    )
                
                # Generate response using the appropriate prompt
                response = self.agent.invoke({
                    "messages": [
                        SystemMessage(content=GreeterPrompts.SYSTEM),
                        SystemMessage(content=prompt),
                        *history,
                        last_message
                    ]
                })
                
                logger.info(f"{self.name} response: {response}")
                return self.create_response(state, self.extract_content(response))
            
            return self.create_response(
                state,
                self.extract_content(self.agent.invoke(state))
            )
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return self.create_response(
                state,
                "I apologize for the error. How can I assist you with phone fraud detection?"
            ) 