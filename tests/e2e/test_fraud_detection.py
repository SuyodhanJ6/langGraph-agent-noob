import pytest
from fastapi.testclient import TestClient
from main import app
from tests.helpers.mock_groq import mock_groq_response
from httpx import AsyncClient
import asyncio
from typing import List
import uuid

class TestFraudDetectionFlow:
    @pytest.fixture
    async def async_client(self):
        """Create async client for testing"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            await asyncio.sleep(0.1)  # Give time for client setup
            yield ac

    @pytest.mark.asyncio
    async def test_complete_fraud_report_flow(self, async_client, test_db):
        """Test the complete flow of reporting a fraudulent number"""
        # Mock GROQ responses for each step
        greeting_response = (
            "Hello! I understand you want to report a fraudulent number. "
            "I'll help you with that process."
        )
        
        number_response = (
            "I've noted the phone number +1-555-123-4567. "
            "Could you please describe the fraudulent activity?"
        )
        
        description_response = (
            "Thank you for reporting this. I've registered your report about "
            "IRS scam calls from +1-555-123-4567."
        )
        
        # Step 1: Initial greeting
        with mock_groq_response(greeting_response):
            response = await async_client.post("/api/v1/chat", json={
                "content": "Hi, I want to report a fraudulent number",
                "session_id": "test_session",
                "user_id": "test_user"
            })
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert greeting_response in data["content"]
        
        await asyncio.sleep(0.1)  # Small delay to ensure message processing
        
        # Step 2: Provide phone number
        with mock_groq_response(number_response):
            response = await async_client.post("/api/v1/chat", json={
                "content": "The number is +1-555-123-4567",
                "session_id": "test_session",
                "user_id": "test_user"
            })
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert number_response in data["content"]
        
        await asyncio.sleep(0.1)  # Small delay to ensure message processing
        
        # Step 3: Provide description
        with mock_groq_response(description_response):
            response = await async_client.post("/api/v1/chat", json={
                "content": "They keep calling claiming to be from the IRS",
                "session_id": "test_session",
                "user_id": "test_user"
            })
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert description_response in data["content"]
        
        await asyncio.sleep(0.1)  # Small delay to ensure database updates
        
        # Verify report was saved in database
        with test_db.get_cursor(dictionary=True) as cursor:
            # Check fraud_reports table
            cursor.execute("""
                SELECT * FROM fraud_reports 
                WHERE phone_number = %s
            """, ("+1-555-123-4567",))
            report = cursor.fetchone()
            assert report is not None
            assert report["is_fraud"] is True
            assert "IRS" in report["description"]
            
            # Check chat_messages table for conversation history
            cursor.execute("""
                SELECT * FROM chat_messages 
                WHERE session_id = %s 
                ORDER BY turn_number
            """, ("test_session",))
            messages = cursor.fetchall()
            assert len(messages) >= 2  # At least user message and response
            
            # Verify message sequence
            user_messages = [m for m in messages if m["role"] == "user"]
            assistant_messages = [m for m in messages if m["role"] == "assistant"]
            
            assert len(user_messages) > 0, "No user messages found"
            assert len(assistant_messages) > 0, "No assistant messages found"
            
            # Verify content
            user_contents = " ".join(m["content"] for m in user_messages)
            assistant_contents = " ".join(m["content"] for m in assistant_messages)
            
            assert "IRS" in user_contents
            assert "+1-555-123-4567" in user_contents
            assert "report" in user_contents.lower()
            assert any(resp in assistant_contents for resp in [
                greeting_response, 
                number_response, 
                description_response
            ])

    @pytest.mark.asyncio
    async def test_concurrent_users(self, test_db):
        """Test system handling multiple concurrent users"""
        
        async def simulate_user_conversation(client: AsyncClient, user_id: str) -> dict:
            """Simulate a complete user conversation flow"""
            session_id = f"session_{uuid.uuid4()}"
            phone_number = f"+1-555-{user_id[-4:]}"  # Generate unique number
            
            # User's greeting
            greeting_response = f"Hello user {user_id}! How can I help you?"
            with mock_groq_response(greeting_response):
                response = await client.post("/api/v1/chat", json={
                    "content": "Hi, I want to report a scam call",
                    "session_id": session_id,
                    "user_id": user_id
                })
                assert response.status_code == 200
            
            await asyncio.sleep(0.1)
            
            # User provides phone number
            number_response = f"I see you want to report {phone_number}. What happened?"
            with mock_groq_response(number_response):
                response = await client.post("/api/v1/chat", json={
                    "content": f"The number is {phone_number}",
                    "session_id": session_id,
                    "user_id": user_id
                })
                assert response.status_code == 200
            
            await asyncio.sleep(0.1)
            
            # User provides description
            description_response = f"Thank you for reporting {phone_number}"
            with mock_groq_response(description_response):
                response = await client.post("/api/v1/chat", json={
                    "content": f"They claimed to be from IRS, user {user_id} reporting",
                    "session_id": session_id,
                    "user_id": user_id
                })
                assert response.status_code == 200
            
            return {
                "user_id": user_id,
                "session_id": session_id,
                "phone_number": phone_number
            }
        
        # Create multiple user conversations
        num_users = 5
        user_tasks = []
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            for i in range(num_users):
                user_id = f"test_user_{i}"
                task = asyncio.create_task(simulate_user_conversation(client, user_id))
                user_tasks.append(task)
            
            # Run all conversations concurrently
            user_results = await asyncio.gather(*user_tasks)
            
            await asyncio.sleep(0.2)  # Give time for database updates
            
            # Verify database state for all users
            with test_db.get_cursor(dictionary=True) as cursor:
                # Check fraud reports
                for user_data in user_results:
                    cursor.execute("""
                        SELECT * FROM fraud_reports 
                        WHERE phone_number = %s
                    """, (user_data["phone_number"],))
                    report = cursor.fetchone()
                    assert report is not None, f"No report found for {user_data['phone_number']}"
                    assert report["is_fraud"] is True
                    assert "IRS" in report["description"]
                    assert user_data["user_id"] in report["description"]
                
                # Check message history
                for user_data in user_results:
                    cursor.execute("""
                        SELECT COUNT(*) as msg_count 
                        FROM chat_messages 
                        WHERE session_id = %s
                    """, (user_data["session_id"],))
                    count = cursor.fetchone()["msg_count"]
                    assert count >= 6, f"Missing messages for session {user_data['session_id']}"
                
                # Verify no cross-contamination
                cursor.execute("SELECT COUNT(DISTINCT user_id) as user_count FROM chat_messages")
                distinct_users = cursor.fetchone()["user_count"]
                assert distinct_users == num_users, "Incorrect number of distinct users"
                
                # Check message ordering within sessions
                for user_data in user_results:
                    cursor.execute("""
                        SELECT role, content, turn_number
                        FROM chat_messages 
                        WHERE session_id = %s 
                        ORDER BY turn_number
                    """, (user_data["session_id"],))
                    messages = cursor.fetchall()
                    
                    # Verify conversation flow
                    roles = [m["role"] for m in messages]
                    assert roles.count("user") >= 3, f"Missing user messages in {user_data['session_id']}"
                    assert roles.count("assistant") >= 3, f"Missing assistant responses in {user_data['session_id']}"
                    
                    # Verify turn ordering
                    turn_numbers = [m["turn_number"] for m in messages]
                    assert turn_numbers == sorted(turn_numbers), f"Incorrect message ordering in {user_data['session_id']}"
                    
                    # Verify content
                    content = " ".join(m["content"] for m in messages)
                    assert user_data["phone_number"] in content, f"Phone number missing in {user_data['session_id']}"
                    assert "IRS" in content, f"Description missing in {user_data['session_id']}"

    @pytest.fixture(autouse=True)
    async def setup_database(self, test_db):
        """Setup required database tables before each test"""
        with test_db.get_cursor() as cursor:
            # Create required tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    phone_number VARCHAR(20),
                    is_fraud BOOLEAN DEFAULT FALSE,
                    report_count INT DEFAULT 0,
                    first_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    description TEXT,
                    reporter_ip VARCHAR(45),
                    INDEX idx_phone (phone_number)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    message_id VARCHAR(100) NOT NULL UNIQUE,
                    session_id VARCHAR(100) NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    role ENUM('user', 'assistant', 'system') NOT NULL,
                    content TEXT NOT NULL,
                    agent_name VARCHAR(50),
                    turn_number INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON,
                    INDEX idx_session_turn (session_id, turn_number)
                )
            """)
            test_db.connection.commit()
            
            # Clean up any existing test data
            cursor.execute("DELETE FROM fraud_reports")
            cursor.execute("DELETE FROM chat_messages")
            test_db.connection.commit()
            
        yield  # Let the test run
        
        # Cleanup after test
        with test_db.get_cursor() as cursor:
            cursor.execute("DELETE FROM fraud_reports")
            cursor.execute("DELETE FROM chat_messages")
            test_db.connection.commit() 