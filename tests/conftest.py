import pytest
from fastapi.testclient import TestClient
from src.database.connection import DatabaseConnection
from main import app
import os
import mysql.connector
from mysql.connector import Error
from langchain_groq import ChatGroq
from tests.config.test_config import TEST_DB_CONFIG, TEST_DB_CONNECT_ARGS, TEST_DB_NAME
import logging

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup and cleanup test database"""
    try:
        # Drop and recreate database
        conn = mysql.connector.connect(
            **TEST_DB_CONFIG,
            **TEST_DB_CONNECT_ARGS,
            allow_local_infile=True
        )
        cursor = conn.cursor(buffered=True)
        
        # Drop database if exists
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        cursor.execute(f"CREATE DATABASE {TEST_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        
        yield
        
        # Cleanup after all tests
        conn = mysql.connector.connect(
            **TEST_DB_CONFIG,
            **TEST_DB_CONNECT_ARGS,
            allow_local_infile=True
        )
        cursor = conn.cursor(buffered=True)
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        cursor.close()
        conn.close()
        
    except Error as e:
        pytest.fail(f"Failed to setup/cleanup test database: {e}")

@pytest.fixture
def test_db():
    """Get database connection for tests"""
    db = DatabaseConnection()
    return db

@pytest.fixture
def test_client(test_db):
    """Create a test client with database"""
    return TestClient(app)

@pytest.fixture
def mock_llm():
    """Create a mock GROQ LLM for testing"""
    return ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0.1,
        api_key="gsk_test_key"
    )

@pytest.fixture
def sample_phone_number():
    return "+1-555-123-4567"

@pytest.fixture
def sample_fraud_report():
    return {
        "phone_number": "+1-555-123-4567",
        "description": "Automated spam calls claiming to be IRS",
        "reporter_ip": "127.0.0.1"
    } 