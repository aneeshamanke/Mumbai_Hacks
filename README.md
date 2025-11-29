# VeriVerse Misinformation Detection Agent

This is a FastAPI-based agent that uses Google Gemini and Tavily Search to verify information and detect misinformation.

## 🛠️ Setup

### 1. Prerequisites
- Python 3.9 or higher
- API Keys for:
  - **Google Gemini** (LLM)
  - **Tavily** (Search)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a file named `config/.env` and add your API keys:
```ini
GEMINI_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here
```

## 🚀 Running the Server

Start the FastAPI server:
```bash
python3 api_gateway/main.py
```
*The server will start on `http://0.0.0.0:8000`.*

## 🧪 Testing the API

You can test the API using `curl` or Postman.

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8000/prompts" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "Is the earth flat?",
           "user_id": "test_user"
         }'
```

**Response Format:**
The API returns a JSON object with:
- `provisional_answer`: The agent's verified answer.
- `confidence`: A score (0.0 - 1.0) indicating confidence.
- `citations`: List of sources used.
- `steps`: The reasoning trace of the agent.
