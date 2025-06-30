# Beach Information AI Assistant

An AI-powered assistant that provides information about beaches in the USA, including weather conditions, tides, and local amenities.

## Features

- Get real-time beach information
- Query tide and weather conditions
- Find nearby amenities and facilities
- Natural language interaction

## Prerequisites

- Python 3.13+
- Ollama with Llama 3.2 running locally
- API keys for external services (Google Places, NOAA, etc.)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd beach-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your API keys:
   ```env
   # Ollama Configuration
   OLLAMA_API_BASE=http://localhost:11434
   
   # Google Places API
   GOOGLE_PLACES_API_KEY=your_google_places_api_key
   
   # NOAA API (if applicable)
   NOAA_API_KEY=your_noaa_api_key
   ```

## Usage

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Access the API documentation at: http://127.0.0.1:8000/docs

## Project Structure

```
beach-ai/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration settings
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic and external services
│   └── utils/           # Utility functions
├── tests/               # Test files
├── .env.example         # Example environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Development

- Run tests:
  ```bash
  pytest
  ```

- Format code:
  ```bash
  black .
  isort .
  ```

## License

MIT
