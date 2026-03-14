# Development Guide

## Getting Started

### Prerequisites
- Python 3.13+
- UV package manager
- Google API key (Gemini)
- Access to Cloudflare Worker (or deploy your own rendezvous agent)

### Initial Setup
```bash
# Clone and navigate to project
cd deployed_a2a_sample

# Install dependencies
uv sync

# Configure environment
cp .env.example .env  # If available, otherwise create .env
# Edit .env with your GOOGLE_API_KEY and other settings
```

### Running Locally

**Option 1: Combined startup (recommended for testing)**
```bash
# Terminal 1: Start agents
uv run python run_agents.py

# Terminal 2: Start frontend
uv run python frontend_app.py

# Access dashboard at http://localhost:8000
```

**Option 2: ADK command (production mode)**
```bash
# Terminal 1: Start agents with ADK
uv run adk api_server . --a2a --port 9000 --log_level warning

# Terminal 2: Start frontend
uv run python frontend_app.py
```

## Development Workflows

### Adding a New Agent

1. **Create agent directory**
```bash
mkdir new_agent
cd new_agent
```

2. **Create agent.json** (agent card)
```json
{
  "name": "new_agent",
  "description": "Description of what this agent does",
  "url": "http://127.0.0.1:9000/a2a/new_agent",
  "skills": ["keyword1", "keyword2", "capability"],
  "agent_id": "new_agent"
}
```

3. **Create agent.py**
```python
from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.models import Gemini
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.discovery_tools import get_discovery_tools

# Get discovery tools with agent identity
discovery_agent_tool, handshake_tool, call_remote_agent_tool = get_discovery_tools("new_agent")

# Define agent-specific tools
def custom_tool() -> str:
    """Tool description for LLM."""
    # Implementation
    return "result"

# Define retry configuration
retry_config = types.HttpRetryOptions(
    attempts=3,
    initial_delay=2,
    exp_base=2,
    http_status_codes=[429, 500, 503]
)

root_agent = Agent(
    model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
    name="new_agent",
    description="Agent description",
    instruction=(
        "Instructions for the agent's behavior.\n"
        "1. Use discovery_agent_tool to find peers\n"
        "2. Use handshake_tool to verify peers\n"
        "3. Use call_remote_agent_tool to delegate tasks"
    ),
    tools=[custom_tool, discovery_agent_tool, handshake_tool, call_remote_agent_tool],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
```

4. **Create __init__.py**
```python
# Empty file or import root_agent if needed
```

5. **Update run_agents.py**
```python
AGENTS_DIRS = ["airline_agent", "travel_agent", "personal_assistant", "new_agent"]
```

### Modifying Agent Behavior

**Update agent instructions:**
- Edit the `instruction` parameter in `agent.py`
- Keep instructions clear and focused on discovery workflow
- Always include guidance on using discovery tools

**Add new tools:**
- Define function with docstring (LLM uses this)
- Add to `tools` list in Agent constructor
- Use `console.print()` for debugging output

**Update agent card:**
- Modify `agent.json` to reflect new capabilities
- Update `skills` array for better discovery matching
- Restart agents for changes to take effect

### Testing

**End-to-End Test:**
```bash
# Ensure agents are running first
uv run python test_e2e.py
```

**Manual Testing via Dashboard:**
1. Start agents and frontend
2. Open http://localhost:8000
3. Use chat interface to send requests
4. Monitor event timeline for agent interactions

**Testing Discovery:**
```python
# In agent tool or test script
from tools.discovery_tools import RendezvousRegistry

registry = RendezvousRegistry()
agents = await registry.find_agents("travel")
print(agents)
```

## Common Development Tasks

### Debugging Agent Interactions

**Enable verbose logging:**
```python
# In agent.py, change log level
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check agent registration:**
```bash
curl https://rendezvous-agent.lveyssier.workers.dev/agents
```

**Verify agent card:**
```bash
# Version 2 (current)
curl http://localhost:9000/a2a/personal_assistant/.well-known/agent-card.json
```

### Modifying Discovery Logic

**Change search algorithm:**
- Edit `RendezvousRegistry.find_agents()` in `tools/discovery_tools.py`
- Current: ALL query words must match
- Alternative: ANY word matches, ranked by relevance

**Adjust cache TTL:**
```python
# In RendezvousRegistry.__init__
self._cache_ttl = 20  # seconds (increase for less registry load)
```

**Customize event reporting:**
```python
# In discovery_tools.py, modify report_event()
# Add more details, change event types, etc.
```

### Frontend Customization

**Add new event types:**
1. Update `report_event()` calls in `discovery_tools.py`
2. Handle new type in `frontend/main.js`
3. Add styling in `frontend/style.css`

**Modify dashboard UI:**
- Edit `frontend/index.html` for structure
- Update `frontend/main.js` for behavior
- Adjust `frontend/style.css` for appearance

## Best Practices

### Agent Design
- Keep agent responsibilities focused and clear
- Use descriptive skill keywords for discovery
- Provide detailed instructions for LLM behavior
- Always filter out self in discovery results

### Tool Design
- Write clear docstrings (LLM reads these)
- Return structured, parseable responses
- Handle errors gracefully with informative messages
- Use async functions for I/O operations

### Discovery Queries
- Use 1-2 generic keywords (e.g., "travel", "hotel")
- Avoid specific details (dates, locations, names)
- Match against agent skills, not full user requests
- Test queries against registry to verify matches

### Error Handling
- Implement retry logic for API calls (see retry_config)
- Validate agent existence before handshake
- Check handshake success before calling
- Provide fallback behavior when discovery fails

### Performance
- Cache registry results (already implemented)
- Use background threads for event reporting
- Minimize heartbeat frequency (30s default)
- Consider connection pooling for high-traffic scenarios

## Deployment Checklist

- [ ] Update `.env` with production values
- [ ] Set `RENDEZVOUS_AGENT_URL` to production registry
- [ ] Configure `PA_AGENT_URL` with production domain
- [ ] Update `FRONTEND_EVENT_URL` with production domain
- [ ] Update agent.json URLs to production endpoints
- [ ] Test health check endpoint: `/api/health`
- [ ] Verify memory usage stays under 512MB
- [ ] Test cold start behavior
- [ ] Confirm heartbeat mechanism works
- [ ] Validate SSE connections remain stable

## Troubleshooting

**Agents not discovering each other:**
- Check registry URL is accessible
- Verify agents registered successfully (check logs)
- Confirm agent cards have correct URLs
- Test discovery query matches agent skills

**Frontend not showing events:**
- Verify `FRONTEND_EVENT_URL` is correct
- Check SSE connection in browser dev tools
- Confirm agents are calling `report_event()`
- Check CORS settings in `frontend_app.py`

**Memory issues on deployment:**
- Use Version 2 (single port) architecture
- Reduce log verbosity (`--log_level warning`)
- Check for memory leaks in custom tools
- Monitor with platform-specific tools

**Agent calls timing out:**
- Increase timeout in `call_remote_agent_tool`
- Check target agent is responsive
- Verify network connectivity between agents
- Review retry configuration
