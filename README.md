# Chhaya OS - Dark Web Monitoring Platform

Chhaya OS is a comprehensive dark web monitoring and intelligence platform designed for cybersecurity professionals. This tool enables automated scanning, analysis, and monitoring of dark web resources with AI-powered insights.

## Prerequisites

- Python 3.10+
- Node.js 16+ (for frontend development)
- Tor service running locally
- Google Gemini API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chhaya-os.git
   cd chhaya-os
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Backend

1. Ensure Tor service is running on localhost:9050
2. Start the FastAPI server:
   ```bash
   cd app
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`

## Running the Frontend

1. Navigate to the static directory:
   ```bash
   cd static
   ```

2. Start the development server:
   ```bash
   python -m http.server 8001
   ```
   The frontend will be available at `http://localhost:8001`

## API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

```
Copyright 2025 Chhaya OS Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Support

For support, please open an issue in the GitHub repository.