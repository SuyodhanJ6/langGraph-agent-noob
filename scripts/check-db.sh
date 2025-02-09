#!/bin/bash
set -e

until mysql -h db -u root -p${DB_PASSWORD} -e "SELECT 1" >/dev/null 2>&1; do
  echo "Waiting for database connection..."
  sleep 5
done

mysql -h db -u root -p${DB_PASSWORD} ${DB_NAME} -e "
  SELECT COUNT(*) FROM information_schema.tables 
  WHERE table_schema = '${DB_NAME}' 
  AND table_name IN ('messages', 'sessions');" | grep -q 2 || {
    echo "Tables not found, initializing database..."
    mysql -h db -u root -p${DB_PASSWORD} ${DB_NAME} < /app/init.sql
} 