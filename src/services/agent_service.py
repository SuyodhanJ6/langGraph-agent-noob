from typing import List, Dict, Any, Union
from langchain_groq import ChatGroq
from src.core.config import settings
from src.utils.logger import logger
from src.models.agents import AgentState, AgentResponse
from src.services.database_service import DatabaseService
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import create_react_agent
from src.tools.tool_factory import ToolFactory
from src.prompts.system_prompts import SystemPrompts
from src.prompts.analysis_prompts import AnalysisPrompts
from src.components.supervisor import Supervisor
from src.components.agents.greeter_agent import GreeterAgent
from src.components.agents.checker_agent import CheckerAgent
from src.components.agents.reporter_agent import ReporterAgent
from src.constants.routes import AgentRoutes
from langchain_core.messages import HumanMessage, AIMessage
from src.models.chat import ChatMessage

class AgentService:
    def __init__(self):
        self.settings = settings
        self.db_service = DatabaseService()
        self.llm = self._init_llm()
        self.tools = ToolFactory()
        self.graph = self._build_graph()
    
    def _init_llm(self) -> ChatGroq:
        return ChatGroq(
            model_name=settings.GROQ_MODEL,
            temperature=0.1,
            api_key=settings.GROQ_API_KEY
        )
    
    def _build_graph(self) -> StateGraph:
        # Create base agents
        checker_base = create_react_agent(
            model=self.llm,
            tools=self.tools.get_checker_tools(),
            prompt=SystemPrompts.CHECKER
        )
        
        reporter_base = create_react_agent(
            model=self.llm,
            tools=self.tools.get_reporter_tools(),
            prompt=SystemPrompts.REPORTER
        )
        
        greeter_base = create_react_agent(
            model=self.llm,
            tools=[],
            prompt=SystemPrompts.GREETER
        )

        # Create agent components
        checker = CheckerAgent(checker_base)
        reporter = ReporterAgent(reporter_base)
        greeter = GreeterAgent(greeter_base)
        supervisor = Supervisor(self.llm, AnalysisPrompts.SUPERVISOR_ANALYSIS)

        # Define nodes
        async def supervisor_node(state: MessagesState) -> Dict:
            result = await supervisor.process(state)
            logger.info(f"Supervisor result: {result}")
            return result

        async def checker_node(state: MessagesState) -> Dict:
            result = await checker.process(state)
            logger.info(f"Checker result: {result}")
            return result

        async def reporter_node(state: MessagesState) -> Dict:
            result = await reporter.process(state)
            logger.info(f"Reporter result: {result}")
            return result

        async def greeter_node(state: MessagesState) -> Dict:
            result = await greeter.process(state)
            logger.info(f"Greeter result: {result}")
            return result

        # Build graph
        workflow = StateGraph(MessagesState)
        
        # Add nodes
        workflow.add_node(AgentRoutes.SUPERVISOR.value, supervisor_node)
        workflow.add_node(AgentRoutes.CHECKER.value, checker_node)
        workflow.add_node(AgentRoutes.REPORTER.value, reporter_node)
        workflow.add_node(AgentRoutes.GREETER.value, greeter_node)
        
        # Define routing function
        def get_next_step(state: MessagesState) -> str:
            """Determine the next step based on state"""
            # Check if we should end the conversation
            if state.get("messages"):
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    logger.info("Ending conversation after agent response")
                    return END

            # Get the next step from state
            next_step = state.get("next", AgentRoutes.GREETER.value)
            logger.info(f"Next step: {next_step}")
            return next_step

        # Add edges with conditions
        workflow.add_conditional_edges(
            AgentRoutes.SUPERVISOR.value,
            lambda x: get_next_step(x)
        )

        # Add direct edges from agents to END
        for agent in [AgentRoutes.CHECKER.value, AgentRoutes.REPORTER.value, AgentRoutes.GREETER.value]:
            workflow.add_conditional_edges(
                agent,
                lambda x: END
            )
        
        # Set entry point
        workflow.set_entry_point(AgentRoutes.SUPERVISOR.value)
        
        return workflow.compile()
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, Any]]) -> List[Union[HumanMessage, AIMessage]]:
        """Convert database messages to langchain messages"""
        converted = []
        for msg in messages:
            if msg['role'] == 'user':
                converted.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                converted.append(AIMessage(
                    content=msg['content'],
                    name=msg.get('name')
                ))
        return converted

    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        user_id: str
    ) -> AgentResponse:
        try:
            logger.info(f"Processing message: {message}")
            
            # Load conversation history
            history = self.db_service.get_session_messages(session_id)
            
            # Convert history to langchain messages
            langchain_history = self._convert_to_langchain_messages(history)
            
            # Create initial state with history and new message
            state = {
                "messages": langchain_history + [HumanMessage(content=message)],
                "session_id": session_id,
                "user_id": user_id
            }
            
            # Save user message to database
            self.db_service.save_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=message
            )
            
            # Process stream and get last response
            last_response = None
            try:
                async for response in self.graph.astream(state):
                    logger.info(f"Stream response: {response}")
                    if isinstance(response, dict):
                        if "messages" in response:
                            last_response = response
                        elif isinstance(response.get(AgentRoutes.CHECKER.value), dict):
                            last_response = response[AgentRoutes.CHECKER.value]
                        elif isinstance(response.get(AgentRoutes.GREETER.value), dict):
                            last_response = response[AgentRoutes.GREETER.value]
                        elif isinstance(response.get(AgentRoutes.REPORTER.value), dict):
                            last_response = response[AgentRoutes.REPORTER.value]
            except Exception as e:
                logger.error(f"Error in stream processing: {str(e)}")
                raise
            
            if not last_response or "messages" not in last_response:
                logger.error(f"Invalid response format: {last_response}")
                raise Exception("No valid response generated")
            
            last_message = last_response["messages"][-1]
            logger.info(f"Final response: {last_message}")
            
            # Save assistant response to database
            self.db_service.save_message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=last_message.content,
                name=getattr(last_message, 'name', None)
            )
            
            return AgentResponse(
                content=last_message.content,
                name=getattr(last_message, 'name', None)
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise 