# BPK Legal Document API

A FastAPI application for searching and retrieving legal documents from [peraturan.bpk.go.id](https://peraturan.bpk.go.id).

## Features

- 🔍 Search for legal documents using natural language queries
- 📄 Extract content from legal documents and PDFs
- 🤖 AI-powered query enhancement and response generation
- 📊 Relevance ranking with IndoBERT embeddings
- 📱 RESTful API with comprehensive documentation
- 📝 Generate HTML reports of search results

## Architecture

The application follows clean architecture principles with the following layers:

- **Domain Layer**: Core business models
- **Service Layer**: Business logic and use cases
- **Infrastructure Layer**: External services and data access
- **API Layer**: REST endpoints and controllers

## Requirements

- Python 3.8+
- FastAPI
- PyPDF2
- OpenAI API key (optional, for LLM features)
- IndoBERT dependencies (optional, for relevance ranking)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ayooke97/aiproduction-development.git
cd aiproduction-development
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
# For production
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt
```

4. Create a `.env` file with your configuration:

```
# API settings
DEBUG=False
API_V1_STR=/api/v1

# OpenAI settings (optional)
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen2.5-72b-instruct

# Scraper settings
MAX_PAGES_DEFAULT=5
MAX_RESULTS_DEFAULT=10
REQUEST_TIMEOUT=30

# Feature toggles
ENABLE_BPK_SCRAPER=True
ENABLE_PERATURAN_SCRAPER=True
ENABLE_OPENAI=True
ENABLE_INDOBERT=True
```

## Usage

### Running the server

```bash
python -m app.main
```

The API will be available at http://localhost:8000.

### API Documentation

API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

#### Search Endpoints

- `POST /api/v1/search/query`: Search with a JSON request body
- `GET /api/v1/search/simple`: Simple search with query parameters
- `POST /api/v1/search/report`: Generate an HTML report of search results

#### Document Endpoints

- `GET /api/v1/documents/{document_id}`: Get a document by ID
- `POST /api/v1/documents/extract-pdf`: Extract content from a PDF URL
- `POST /api/v1/documents/upload-pdf`: Upload and extract content from a PDF file

### Example Request

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/search/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "hak tanah ulayat",
  "preferences": {
    "verbosity": "detailed",
    "format": "simple",
    "citations": true,
    "max_results": 5
  }
}'
```

## Testing

The project has a comprehensive test suite with unit, integration, and end-to-end tests.

### Test Structure

```
tests/
├── conftest.py             # pytest configuration and fixtures
├── test_main.py            # Tests for main application
├── unit/                   # Unit tests
│   ├── core/               # Tests for core functionality
│   ├── domain/             # Tests for domain models
│   ├── infrastructure/     # Tests for infrastructure components
│   ├── services/           # Tests for services
│   └── utils/              # Tests for utilities
├── integration/            # Integration tests
│   ├── test_api_routes.py  # Tests for API routes
│   ├── test_scrapers.py    # Tests for scrapers
│   └── test_services.py    # Tests for services
└── e2e/                    # End-to-end tests
    └── test_api.py         # Tests for full API flows
```

### Running Tests

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app
```

Run specific test categories:

```bash
# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest -m integration

# Run end-to-end tests only
pytest -m e2e
```

Generate HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

### Using the Test Client

The examples directory contains a simple test client (`examples/client.py`) that demonstrates how to use the API:

```bash
python examples/client.py
```

## Optional Dependencies

The application supports the following optional dependencies:

- **Sastrawi**: For Indonesian stemming
- **OpenAI**: For query enhancement and response generation
- **IndoBERT**: For document relevance ranking

## Development

### Linting and Formatting

```bash
# Run Black formatter
black app tests

# Run isort to sort imports
isort app tests

# Run flake8 linter
flake8 app tests

# Run pylint
pylint app tests

# Run mypy type checker
mypy app tests
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

This will automatically run linting and formatting on each commit.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
