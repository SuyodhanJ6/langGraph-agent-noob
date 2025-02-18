# Phone Fraud Detection System

A smart system for detecting and reporting fraudulent phone numbers using LangChain and FastAPI.

## 🤖 Agent Architecture
![Fraud Detection Agent Architecture](media/images/fraud_detection_graph.png)

## 📊 System Architecture
![Phone Fraud Detection System Architecture](media/images/PhoneFraudFunctionalHLD.png)

Our system uses a multi-agent architecture powered by LangGraph:
- **Supervisor Agent**: Routes user messages to specialized agents
- **Greeter Agent**: Handles introductions and general queries
- **Checker Agent**: Verifies phone numbers against fraud database
- **Reporter Agent**: Processes fraud reports and updates database

## 🚀 Quick Start

### 🔧 Local Development Setup

1. Install uv:
```bash
pip install uv
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv lock
uv sync --frozen
```

4. Set up MySQL:
   - Install MySQL Server
   - Create database: `noob_busts_scams`
   - Configure `.env` with your database credentials

5. Run the application:
```bash
uvicorn main:app --reload
```

### 🐳 Docker Setup

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Stop containers:
```bash
docker-compose down
```

3. Clean up volumes (if needed):
```bash
docker-compose down -v
```

## 🌐 API Endpoints

- `POST /api/v1/chat`: Send messages to the fraud detection system
- `GET /api/v1/health`: Check system health

## 🛠️ Configuration

### Local Environment (.env)
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=noob_busts_scams
```

### Docker Environment (.env.docker)
```env
DB_HOST=db
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=noob_busts_scams
```

## 📁 Project Structure
```
.
├── controller/              # API controllers
│   ├── routers/            # API route definitions
│   └── service/            # Service layer
├── src/
│   ├── components/         # Agent components
│   ├── core/              # Core configurations
│   ├── database/         # Database connections
│   ├── models/          # Data models
│   ├── prompts/        # LLM prompts
│   ├── services/      # Business logic
│   ├── tools/        # LangChain tools
│   └── utils/       # Utilities
├── docker/
│   └── Dockerfile   # Docker configuration
├── docker-compose.yaml    # Docker services definition
├── main.py              # Application entry point
├── pyproject.toml      # Project dependencies
└── README.md          # Documentation
```

## 🔍 Features

- Phone number fraud checking
- Fraud reporting system
- Conversation history
- Smart agent routing
- Database persistence

## 🚀 Development

### Adding New Dependencies

1. Add to `pyproject.toml`:
```toml
[project]
dependencies = [
    "new-package~=1.0.0",
]
```

2. Update dependencies:
```bash
uv lock
uv sync --frozen
```

### Running Tests

1. Install test dependencies:
```bash
uv pip install -e ".[test]"
```

2. Run all tests:
```bash
pytest
```

3. Run specific test categories:
```bash
pytest tests/unit/  # Unit tests only
pytest tests/integration/  # Integration tests only
pytest tests/e2e/  # End-to-end tests only
```

4. Generate coverage report:
```bash
pytest --cov=src --cov-report=html
```

## 🐛 Troubleshooting

### Common Issues

1. Database Connection:
   - Check if MySQL is running
   - Verify credentials in `.env` or `.env.docker`
   - For Docker: ensure port 3308 is free

2. Docker Issues:
   - Port conflicts: modify ports in `docker-compose.yaml`
   - Clean rebuild: `docker-compose down -v && docker-compose up --build`

### Logs

- Docker logs: `docker-compose logs -f`
- Application logs: Check `logs/` directory

## 📝 License

MIT License - see LICENSE file for details


