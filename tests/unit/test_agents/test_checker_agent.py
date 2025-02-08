import pytest
from src.components.agents.checker_agent import CheckerAgent
from langchain_core.messages import HumanMessage
from unittest.mock import Mock, patch
from langchain_groq import ChatGroq

class TestCheckerAgent:
    @pytest.fixture
    def mock_llm(self):
        return ChatGroq(
            model_name="llama-3.1-8b-instant",
            temperature=0.1,
            api_key="gsk_test_key"
        )
    
    @pytest.fixture
    def checker_agent(self, mock_llm):
        agent = Mock()
        agent.llm = mock_llm
        return CheckerAgent(agent)
    
    @pytest.mark.asyncio
    async def test_extract_phone_number(self, checker_agent):
        # Test various phone number formats
        test_cases = [
            ("+1-555-123-4567", "+1-555-123-4567"),
            ("5551234567", "+1-555-123-4567"),
            ("555-123-4567", "+1-555-123-4567"),
            ("(555) 123-4567", "+1-555-123-4567"),
        ]
        
        for input_number, expected in test_cases:
            result = checker_agent._extract_phone_number(input_number)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_process_valid_number(self, checker_agent):
        state = {
            "messages": [HumanMessage(content="Check this number: +1-555-123-4567")]
        }
        
        response = await checker_agent.process(state)
        assert "messages" in response
        assert "I found the phone number" in response["messages"][-1].content
    
    @pytest.mark.asyncio
    async def test_process_invalid_number(self, checker_agent):
        state = {
            "messages": [HumanMessage(content="Check this number: invalid")]
        }
        
        response = await checker_agent.process(state)
        assert "messages" in response
        assert "need a valid phone number" in response["messages"][-1].content.lower() 