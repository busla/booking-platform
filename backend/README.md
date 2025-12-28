# Quesada Apartment Booking Backend

Agent-First Vacation Rental Booking Platform - Backend powered by Strands Agents.

## Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"
```

## Development

```bash
# Run development server
python -m uvicorn src.api:app --reload --port 3001

# Run tests
pytest

# Run linting
ruff check src tests

# Run type checking
mypy src
```

## Project Structure

```
backend/
├── src/
│   ├── agent/        # Strands agent definition
│   ├── tools/        # @tool decorated functions
│   ├── models/       # Pydantic data models
│   ├── services/     # Business logic
│   └── api/          # FastAPI endpoints
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```
