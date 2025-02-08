TEST_DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Your MySQL root user
    "password": "Prasahnt@123",  # Your MySQL root password
    "port": 3306,
    "use_pure": True,
    "raise_on_warnings": True,
    "connection_timeout": 10,
    "buffered": True
}

TEST_DB_CONNECT_ARGS = {
    "auth_plugin": "mysql_native_password",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}

TEST_DB_NAME = "test_fraud_detection" 