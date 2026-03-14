# Tech Stack

## Backend (Python Agents)

- **Framework**: Google ADK (Agent Development Kit) with A2A protocol support
- **Language**: Python 3.13+
- **Package Manager**: UV (not pip)
- **LLM Provider**: Google Gemini (gemini-2.0-flash)
- **Agent Framework**: Google ADK Agents with LLM-based orchestration
- **HTTP Client**: httpx (async support)
- **Terminal Output**: rich (formatted console output)
- **Server**: Uvicorn (ASGI server)

## Frontend (Dashboard)

- **Framework**: FastAPI (backend for frontend)
- **Static Files**: HTML/CSS/JavaScript (vanilla)
- **Real-Time Communication**: SSE (Server-Sent Events) via sse-starlette
- **HTTP Client**: httpx (for agent communication)

## Infrastructure

- **Rendezvous Registry**: Cloudflare Worker (serverless)
- **Deployment Platforms**: Railway-deactivated, Koyeb-paused (512MB RAM constraint), Azure (active)

## Key Libraries

### Python Dependencies
- `google-adk[a2a]>=1.22.1` - Agent Development Kit with A2A protocol
- `rich>=13.0.0` - Terminal formatting
- `httpx>=0.27.0` - Async HTTP client
- `python-dotenv>=1.2.1` - Environment variable management
- `fastapi>=0.123.10` - Web framework for frontend app
- `uvicorn>=0.40.0` - ASGI server
- `sse-starlette>=3.2.0` - Server-Sent Events support

## Common Commands

### Development (Version 1 - Multi-Port)
```bash
uv sync                              # Install/update dependencies
uv run python run_agents.py          # Start all agents (ports 9000-9002)
uv run python frontend_app.py        # Start frontend dashboard (port 8000)
uv run python test_e2e.py           # Run end-to-end test
```

### Production (Version 2 - Single Port)
```bash
uv sync                              # Install/update dependencies
uv run adk api_server . --a2a --port 9000 --log_level warning  # Start all agents
uv run python frontend_app.py        # Start frontend dashboard (port 8000)
```

### Combined Startup
```bash
python run_agents.py & python frontend_app.py  # Both processes (Railway/Koyeb)
```

## Environment Variables

### Required (.env in root)
- `GOOGLE_API_KEY`: Google Gemini API key
- `RENDEZVOUS_AGENT_URL`: Cloudflare Worker endpoint (default: https://rendezvous-agent.lveyssier.workers.dev)
- `FRONTEND_EVENT_URL`: Frontend trace endpoint (default: http://localhost:8000/api/trace)
- `PA_AGENT_URL`: Personal Assistant endpoint (default: http://127.0.0.1:9000/a2a/personal_assistant)

### Optional
- `PORT`: Frontend port (default: 8000, auto-detected on cloud platforms)

## Agent Card Protocol

Each agent exposes its card at:
- **Version 1**: `http://localhost:<port>/.well-known/agent-card.json`
- **Version 2**: `http://localhost:9000/a2a/<agent_name>/.well-known/agent-card.json`

## Development Setup

1. Install UV: Follow https://docs.astral.sh/uv/getting-started/installation/
2. Sync dependencies: `uv sync`
3. Configure `.env` with required variables
4. Start agents: `uv run python run_agents.py`
5. Start frontend: `uv run python frontend_app.py` (separate terminal)
6. Access dashboard: http://localhost:8000

## Deployment Considerations

- **Memory**: Version 2 uses ~350-450MB (fits 512MB limit)
- **Ports**: Single port (9000) for all agents in production
- **Health Checks**: `/api/health` endpoint with ready state
- **Proxy Headers**: Enabled for load balancer compatibility
- **Keep-Alive**: 75s timeout for cloud platform compatibility
