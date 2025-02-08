import pytest
from fastapi.testclient import TestClient
from main import app

class TestChatEndpoints:
    @pytest.fixture
    def client(self, test_db):
        return TestClient(app)
    
    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_chat_endpoint_greeting(self, client, test_db):
        payload = {
            "content": "Hi, I want to check a phone number",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
    
    def test_chat_endpoint_check_number(self, client, test_db):
        payload = {
            "content": "Check this number: +1-555-123-4567",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data 