# Project Structure

## Root Layout

```
/                                    # Project root
├── airline_agent/                   # Airline booking agent
├── travel_agent/                    # Travel coordination agent
├── personal_assistant/              # User-facing assistant agent
├── tools/                           # Shared discovery/registry tools
├── rendezvous-agent/                # Cloudflare Worker registry
├── frontend/                        # Dashboard static files
├── public/                          # Public assets
├── .venv/                           # Python virtual environment
├── .adk/                            # ADK artifacts
├── frontend_app.py                  # FastAPI frontend server
├── run_agents.py                    # Agent startup orchestrator
├── test_e2e.py                      # End-to-end test
├── pyproject.toml                   # UV dependencies
└── .env                             # Environment configuration
```

## Agent Structure (airline_agent, travel_agent, personal_assistant)

Each agent directory follows the same pattern:

```
<agent_name>/
├── __init__.py                      # Python package marker
├── agent.py                         # Agent definition and logic
├── agent.json                       # Agent card metadata
└── .adk/                            # ADK-specific artifacts
```

### agent.py Pattern
- Imports Google ADK Agent class and Gemini model
- Imports discovery tools from `tools/discovery_tools.py`
- Defines agent-specific tools (e.g., `get_passport` for PA)
- Creates `root_agent` with:
  - Model configuration (Gemini 2.0 Flash with retry options)
  - Name, description, instructions
  - Tools list (agent-specific + discovery tools)
  - Safety settings

### agent.json Pattern
- `name`: Agent identifier (e.g., "personal_assistant")
- `description`: Human-readable purpose
- `url`: Agent endpoint (changes between Version 1 and 2)
- `skills`: Array of capability keywords for discovery
- `agent_id`: Unique identifier for registry

## Tools Directory

```
tools/
├── __init__.py
└── discovery_tools.py               # Shared A2A protocol tools
```

### discovery_tools.py Components
- `RendezvousRegistry`: Class for registry interaction
- `get_discovery_tools(agent_name)`: Factory returning agent-specific tools
  - `discovery_agent_tool`: Search registry by capability
  - `handshake_tool`: Verify peer status and get card
  - `call_remote_agent_tool`: Delegate task to remote agent
- `register_to_rendezvous(agent_card_path)`: Registration + heartbeat
- `report_event()`: Send events to frontend for visualization

## Frontend Structure

```
frontend/
├── index.html                       # Dashboard UI
├── main.js                          # Event handling and rendering
└── style.css                        # Dashboard styling
```

### frontend_app.py (FastAPI Server)
- `/api/health`: Health check with agent readiness
- `/api/chat`: Proxy user messages to Personal Assistant
- `/api/trace`: Receive event reports from agents
- `/api/events`: SSE endpoint for real-time event streaming
- `/`: Static file serving for dashboard

## Rendezvous Agent (Cloudflare Worker)

```
rendezvous-agent/
├── src/
│   └── index.ts                     # Worker logic
├── wrangler.toml                    # Cloudflare configuration
└── node_modules/                    # Worker dependencies
```

### Registry API Endpoints
- `POST /register`: Register/refresh agent
- `POST /heartbeat`: Keep agent alive
- `GET /agents`: List live agents
- `DELETE /unregister`: Graceful removal

## Key Architectural Patterns

### Agent Discovery Flow
1. Agent calls `discovery_agent_tool(query)` with capability keywords
2. Tool queries rendezvous registry `/agents` endpoint
3. Registry returns matching agents based on name/description/skills
4. Tool filters out self and returns peer list

### Agent Handshake Flow
1. Agent calls `handshake_tool(target_agent_name)`
2. Tool looks up agent URL in registry
3. Tool fetches `/.well-known/agent-card.json` from peer
4. Returns updated card with current capabilities

### Agent Call Flow
1. Agent calls `call_remote_agent_tool(target, payload, context)`
2. Tool constructs JSON-RPC 2.0 message
3. Tool POSTs to target agent URL
4. Tool extracts response from history
5. Events reported to frontend at each step

### Event Reporting Pattern
- All discovery tools call `report_event()` after operations
- Events sent to `FRONTEND_EVENT_URL` in background thread
- Frontend receives via `/api/trace` and broadcasts via SSE
- Dashboard subscribes to `/api/events` for real-time updates

## Configuration Files

- `pyproject.toml`: UV dependencies (google-adk, fastapi, httpx, etc.)
- `.env`: Environment variables (API keys, URLs)
- `wrangler.toml`: Cloudflare Worker configuration
- `agent.json` (per agent): Agent card metadata

## Data Flow

### User Request Flow
1. User sends message via dashboard → `/api/chat`
2. Frontend proxies to Personal Assistant via JSON-RPC
3. PA processes with discovery/handshake/call tools
4. Response propagates back through agent chain
5. Final response returned to user

### Event Visualization Flow
1. Agent tool calls `report_event()` during operations
2. Event POSTed to `/api/trace` in background thread
3. Frontend adds to event history and broadcasts via SSE
4. Dashboard receives via `/api/events` EventSource
5. UI updates timeline with event details

## Version Differences

### Version 1 (Multi-Port)
- Each agent runs on separate port (9000, 9001, 9002)
- Agent cards at: `http://localhost:<port>/.well-known/agent-card.json`
- Higher memory usage (~600MB+)
- Separate `uvicorn` process per agent

### Version 2 (Single Port - Current)
- All agents on port 9000 via ADK
- Agent cards at: `http://localhost:9000/a2a/<agent_name>/.well-known/agent-card.json`
- Lower memory usage (~350-450MB)
- Single ADK server process
- Requires agent-specific discovery tools (no `os.environ["AGENT_NAME"]`)
