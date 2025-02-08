from src.utils.logger import logger
from src.constants.routes import AgentRoutes
from typing import Dict, Any
import json
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END

class Supervisor:
    def __init__(self, llm, analysis_prompt):
        self.llm = llm
        self.analysis_prompt = analysis_prompt
    
    def format_history(self, messages: list) -> str:
        """Format conversation history for the prompt"""
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                agent_name = getattr(msg, 'name', 'Assistant')
                formatted.append(f"{agent_name}: {msg.content}")
        return "\n".join(formatted)
    
    def clean_json_response(self, content: str) -> str:
        """Clean and extract JSON from LLM response"""
        try:
            # Remove any leading/trailing whitespace
            content = content.strip()
            
            # Find the first '{' and last '}'
            start = content.find('{')
            end = content.rfind('}')
            
            if start >= 0 and end > start:
                # Extract just the JSON part
                json_str = content[start:end + 1]
                
                # Try to parse it to validate
                json.loads(json_str)
                return json_str
            
            raise ValueError("No valid JSON found in response")
            
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {e}")
            logger.error(f"Original content: {content}")
            # Return a default response
            return json.dumps({
                "decision": {
                    "selected_agent": "greeter",
                    "reasoning": "Error parsing response, defaulting to greeter"
                }
            })
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Supervisor node processing...")
            last_message = state["messages"][-1]
            history = state["messages"][:-1]
            
            # If last message was from an agent, we're done
            if isinstance(last_message, AIMessage):
                logger.info("Last message was from agent, ending conversation")
                return {
                    "messages": state["messages"],
                    "next": END
                }
            
            current_msg = last_message.content if isinstance(last_message, (dict, HumanMessage)) else last_message.content
            history_str = self.format_history(history)
            
            # Format prompt
            analysis_prompt = self.analysis_prompt.format(
                current_message=current_msg,
                conversation_history=history_str
            )
            
            logger.info(f"Supervisor analyzing message: {current_msg}")
            response = self.llm.invoke([{
                "role": "system",
                "content": analysis_prompt
            }])
            
            try:
                # Clean and parse the response
                json_str = self.clean_json_response(response.content)
                analysis = json.loads(json_str)
                
                # Extract the decision
                next_agent = analysis['decision']['selected_agent']
                reasoning = analysis['decision']['reasoning']
                
                logger.info(f"Supervisor selected agent: {next_agent} (Reason: {reasoning})")
                
                # Return state with next agent
                return {
                    "messages": state["messages"],
                    "next": next_agent if next_agent != AgentRoutes.FINISH.value else END
                }
                
            except Exception as e:
                logger.error(f"Error parsing supervisor response: {e}")
                logger.error(f"Raw response: {response.content}")
                return {
                    "messages": state["messages"],
                    "next": AgentRoutes.GREETER.value
                }
            
        except Exception as e:
            logger.error(f"Supervisor error: {str(e)}")
            return {
                "messages": state["messages"],
                "next": AgentRoutes.GREETER.value
            } 