# AI Capability Service

A unified AI capability invocation backend service built with **FastAPI**.  
Submit a capability name and input payload via a single endpoint to run various AI tasks.

## Features

| Feature | Status |
|---------|--------|
| Unified `/v1/capabilities/run` endpoint | ✅ |
| `text_summary` capability | ✅ |
| `sentiment_analysis` capability | ✅ |
| Mock mode (no API key needed) | ✅ |
| Real model mode (DeepSeek / Qwen / OpenAI) | ✅ |
| Multi-provider support with runtime switching | ✅ |
| Request logging & elapsed time | ✅ |
| Plugin architecture (easy to add new capabilities) | ✅ |
| Docker support | ✅ |
| Interactive API docs (Swagger UI) | ✅ |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure model providers

```bash
cp .env.example .env
# .env already includes DeepSeek and Qwen API keys
# Edit DEFAULT_PROVIDER to switch between: deepseek / qwen / openai
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### Alternative: Docker

```bash
docker compose up --build
```

## API Examples

### Text Summary (using default provider)

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_summary",
    "input": {
      "text": "Artificial intelligence is transforming every industry. From healthcare to finance, AI-powered tools are helping professionals make better decisions faster. Machine learning models can now process vast amounts of data and identify patterns that would take humans years to discover.",
      "max_length": 80
    },
    "request_id": "demo-001"
  }'
```

### Text Summary (specify provider)

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_summary",
    "input": {
      "text": "Artificial intelligence is transforming every industry.",
      "max_length": 80,
      "provider": "qwen"
    },
    "request_id": "demo-003"
  }'
```

### Sentiment Analysis

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "sentiment_analysis",
    "input": {
      "text": "This product is absolutely amazing and I love using it every day!"
    },
    "request_id": "demo-002"
  }'
```

### List Available Capabilities

```bash
curl http://localhost:8000/v1/capabilities/
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Architecture

```
app/
├── main.py                 # FastAPI entry-point & app factory
├── config.py               # pydantic-settings configuration
├── exceptions.py           # Custom exceptions & error codes
├── schemas/
│   └── capability.py       # Request/response Pydantic models
├── routers/
│   └── capability.py       # POST /v1/capabilities/run
├── services/
│   └── capability_registry.py  # Plugin registry
├── capabilities/
│   ├── base.py             # Abstract base class
│   ├── text_summary.py     # Text summarisation
│   └── sentiment_analysis.py   # Sentiment analysis
└── middleware/
    └── logging.py          # Request logging & timing
```

### Adding a New Capability

1. Create a new file in `app/capabilities/`
2. Subclass `BaseCapability` and implement `name` + `execute`
3. Register the instance in `app/services/capability_registry.py`

That's it — no router changes needed.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug logging & hot-reload |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DEFAULT_PROVIDER` | `deepseek` | Default LLM provider (`deepseek` / `qwen` / `openai`) |
| `DEEPSEEK_API_KEY` | *(empty)* | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | DeepSeek API base URL |
| `DEEPSEEK_MODEL` | `deepseek-chat` | DeepSeek model name |
| `QWEN_API_KEY` | *(empty)* | Qwen (DashScope) API key |
| `QWEN_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Qwen API base URL |
| `QWEN_MODEL` | `qwen-plus` | Qwen model name |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (optional) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |

