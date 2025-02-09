FROM python:3.12.3-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first
COPY pyproject.toml ./

# Create venv and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install mysql-connector-python && \
    uv pip install --no-cache-dir -e .[dev] && \
    uv pip install --no-cache-dir "uvicorn[standard]"

# Copy application code
COPY . .

# Verify installation
RUN . .venv/bin/activate && \
    python --version && \
    python -c "import uvicorn; print(f'uvicorn version: {uvicorn.__version__}')" && \
    ls -la .venv/bin/python

# Set Python path to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Create entrypoint script
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo 'cd /app' >> /entrypoint.sh && \
    echo 'exec python -m uvicorn main:app --host 0.0.0.0 --port 8000' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Run the application
ENTRYPOINT ["/entrypoint.sh"]
