# Import necessary packages
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create tools with error handling
def initialize_tools():
    if not os.getenv("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY not found in .env file. Please set it first.")
    
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY not found in .env file. Please set it first.")
    
    tavily_tool = TavilySearchResults(max_results=5)
    repl = PythonREPL()
    
    return tavily_tool, repl

try:
    tavily_tool, repl = initialize_tools()
except ValueError as e:
    print(f"Error initializing tools: {e}")
    print("\nPlease add these to your .env file:")
    print("TAVILY_API_KEY='your-tavily-key'")
    print("GROQ_API_KEY='your-groq-key'")
    exit(1)

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code and do math. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"

# Create Agent Supervisor
members = ["researcher", "coder"]
options = members + ["FINISH"]

system_prompt = """You are a supervisor tasked with managing a conversation between the following workers:
- researcher: Searches for information online but NEVER does calculations
- coder: Handles all mathematical calculations and coding tasks

Given the user request, respond with the worker to act next. When a calculation is needed, ALWAYS choose 'coder'.
Respond with ONLY ONE of these options: researcher, coder, or FINISH.

Examples:
- For "What's 2+2?": respond with "coder"
- For "Who is Einstein?": respond with "researcher"
- For "What's the square root of 42?": respond with "coder"
"""

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]

# Initialize Groq model
llm = ChatGroq(
    model_name="mixtral-8x7b-32768",
    temperature=0.1,
    max_tokens=4096
)

class State(MessagesState):
    next: str

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    try:
        messages = [
            {"role": "system", "content": system_prompt + "\nRespond with ONLY ONE of these options: researcher, coder, or FINISH."},
        ] + state["messages"]
        
        # Get raw response instead of structured output
        response = llm.invoke(messages)
        response_text = response.content.strip().upper()
        
        # Parse the response
        goto = None
        if "RESEARCHER" in response_text:
            goto = "researcher"
        elif "CODER" in response_text:
            goto = "coder"
        elif "FINISH" in response_text:
            goto = END
        else:
            # If we already have a final answer, end
            if any(msg.get("name") in ["researcher", "coder"] for msg in state["messages"]):
                goto = END
            else:
                print(f"Unclear response from supervisor: {response_text}")
                goto = END
            
        return Command(goto=goto, update={"next": goto})
    except Exception as e:
        print(f"Supervisor error: {str(e)}")
        return Command(goto=END, update={"next": "error"})

# Create specialized agents
def create_research_agent():
    return create_react_agent(
        llm, 
        tools=[tavily_tool], 
        prompt="""You are a researcher. Your role is to search for information online.
        NEVER perform calculations - always defer mathematical operations to the coder.
        If the query involves any math, respond that this should be handled by the coder."""
    )

def create_code_agent():
    return create_react_agent(
        llm, 
        tools=[python_repl_tool],
        prompt="""You are a coder specializing in mathematical calculations and coding tasks.
        When performing calculations:
        1. ALWAYS use the python_repl_tool to ensure accuracy
        2. Show your work by printing intermediate steps
        3. Provide a clear final answer with appropriate context
        4. Include the exact value and mention if it's been rounded
        
        Example response format:
        "I calculated this using Python:
        [show calculation steps]
        The final result is [exact value], which is approximately [rounded value] when rounded to 4 decimal places."
        """
    )

# Worker nodes
def research_node(state: State) -> Command[Literal["supervisor"]]:
    try:
        research_agent = create_research_agent()
        result = research_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="researcher")
                ]
            },
            goto="supervisor",
        )
    except Exception as e:
        print(f"Research node error: {str(e)}")
        return Command(goto="supervisor", update={"messages": [HumanMessage(content=f"Error in research: {str(e)}", name="researcher")]})

def code_node(state: State) -> Command[Literal["supervisor"]]:
    try:
        code_agent = create_code_agent()
        result = code_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="coder")
                ]
            },
            goto="supervisor",
        )
    except Exception as e:
        print(f"Code node error: {str(e)}")
        return Command(goto="supervisor", update={"messages": [HumanMessage(content=f"Error in coding: {str(e)}", name="coder")]})

# Build the graph
def create_multi_agent_graph():
    try:
        builder = StateGraph(State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("researcher", research_node)
        builder.add_node("coder", code_node)
        
        # Compile the graph
        graph = builder.compile()
        
        # Save the graph visualization
        try:
            # Create 'images' directory if it doesn't exist
            os.makedirs('images', exist_ok=True)
            
            # Generate and save the graph image
            graph_image = graph.get_graph().draw_mermaid_png()
            with open('images/multi_agent_graph.png', 'wb') as f:
                f.write(graph_image)
            print("Graph visualization saved to images/multi_agent_graph.png")
        except Exception as e:
            print(f"Warning: Could not save graph visualization: {e}")
        
        return graph
    except Exception as e:
        print(f"Graph creation error: {str(e)}")
        return None

# Example usage
def run_multi_agent_system(query: str):
    try:
        # Check for API keys
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY not found in environment variables")
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY not found in environment variables")
            
        graph = create_multi_agent_graph()
        if not graph:
            return
            
        print("Processing query:", query)
        for s in graph.stream(
            {"messages": [("user", query)]}, 
            subgraphs=True
        ):
            print(s)
            print("----")
            
    except Exception as e:
        print(f"Error running multi-agent system: {str(e)}")

# Test the system
if __name__ == "__main__":
    run_multi_agent_system("What's the square root of 42?")