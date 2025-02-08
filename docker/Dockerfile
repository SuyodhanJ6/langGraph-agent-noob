FROM python:3.12.3-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Create venv and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install mysql-connector-python && \
    uv sync --frozen

# Copy application code
COPY src/ ./src/
COPY controller/ ./controller/
COPY main.py .

# Copy and rename Docker environment file
COPY .env.docker .env

# Install the project in editable mode
RUN . .venv/bin/activate && \
    uv pip install -e . && \
    uv pip install mysql-connector-python

# Expose port
EXPOSE 8000

# Set Python path to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]