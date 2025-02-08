from unittest.mock import patch
import asyncio

def mock_groq_response(content: str):
    """Helper to mock GROQ API responses"""
    async def mock_invoke(*args, **kwargs):
        return {"content": content}
    
    return patch('langchain_groq.ChatGroq.ainvoke', new=mock_invoke)

# Usage example:
"""
def test_something():
    with mock_groq_response("Test response") as mock:
        result = agent.process(...)
        assert "Test response" in result
""" 