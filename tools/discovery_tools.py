import json
import logging
import warnings
import httpx
import asyncio
import uuid
import os
import threading
import time
from typing import Dict, Any, Optional, List
from rich.console import Console

warnings.filterwarnings("ignore", category=UserWarning, module="google.adk.*")

console = Console()
logger = logging.getLogger(__name__)

# Constants

# Constants
RENDEZVOUS_AGENT_URL = "https://rendezvous-agent.lveyssier.workers.dev"
AGENT_CARD_WELL_KNOWN_PATH = "/.well-known/agent-card.json"
HEARTBEAT_INTERVAL = 30  # seconds

class RendezvousRegistry:
    """Manages agent registration and discovery via Cloudflare Rendezvous Agent."""
    
    def __init__(self, base_url: str = RENDEZVOUS_AGENT_URL):
        self.base_url = base_url.rstrip('/')
        self._agents_cache = []
        self._last_fetch = 0
        self._cache_ttl = 10  # seconds

    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Fetch all live agents from the rendezvous agent."""
        now = time.time()
        if now - self._last_fetch < self._cache_ttl and self._agents_cache:
            return self._agents_cache
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/agents", timeout=10.0)
                if response.status_code == 200:
                    self._agents_cache = response.json()
                    self._last_fetch = now
                    return self._agents_cache
                else:
                    logger.error(f"Failed to fetch agents: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching agents: {e}")
            return []

    async def find_agents(self, query: str) -> List[Dict[str, Any]]:
        """Find agents matching the query based on name, description, or skills."""
        agents = await self.get_all_agents()
        query = query.lower()
        matches = []
        for agent in agents:
            name = agent.get('name', '').lower()
            description = agent.get('description', '').lower()
            skills = json.dumps(agent.get('skills', [])).lower()
            
            if query in name or query in description or query in skills:
                matches.append(agent)
        return matches

    async def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a specific agent by name."""
        agents = await self.get_all_agents()
        for agent in agents:
            if agent.get('name') == name:
                return agent
        return None

# Global registry instance
registry = RendezvousRegistry()

async def discovery_agent_tool(query: str) -> str:
    """
    Search for an agent matching the query.
    
    Args:
        query: Keywords to match against agent name, description, or skills.
    Returns:
        A formatted string listing matching agents and their card URLs.
    """
    matches = await registry.find_agents(query)
    if not matches:
        return f"No agent found for query: {query}"
    
    result = "Found the following matching agents:\n"
    for agent in matches:
        result += f"- Agent: {agent['name']}\n  Description: {agent['description']}\n  URL: {agent['url']}\n"
    return result

async def handshake_tool(agent_name: str) -> str:
    """
    Check if an agent is up and running and retrieve its current agent card.
    
    Args:
        agent_name: The name of the agent to check.
    Returns:
        The agent's card information or an error message.
    """
    agent = await registry.get_agent_by_name(agent_name)
    if not agent:
        return f"Error: Agent '{agent_name}' not found in registry. Use discovery_agent_tool first."
    
    card_url = f"{agent['url'].rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(card_url, timeout=10.0)
            if response.status_code == 200:
                card_data = response.json()
                card_data['__url__'] = agent['url']
                console.print(f"Handshake successful with [bold yellow]{agent_name.capitalize()}[/bold yellow]")
                return f"Handshake successful for {agent_name}. Updated Agent Card:\n{json.dumps(card_data, indent=2)}"
            else:
                return f"Handshake failed for {agent_name}. Status code: {response.status_code}"
    except Exception as e:
        return f"Handshake failed for {agent_name}. Error: {str(e)}"

async def call_remote_agent_tool(agent_name: str, payload: str, task_context: Optional[str] = None) -> str:
    """
    Call a remote agent with a specific payload (task description or JSON).
    
    Args:
        agent_name: The name of the agent to call.
        payload: The input to send to the agent.
        task_context: Optional previous context or history to include for statefulness.
    Returns:
        The agent's response.
    """
    agent_info = await registry.get_agent_by_name(agent_name)
    if not agent_info:
        return f"Error: Agent '{agent_name}' not found."
    
    agent_url = agent_info['url']
    
    final_text = payload
    if task_context:
        final_text = f"CONTEXT:\n{task_context}\n\nTASK:\n{payload}"
    
    rpc_payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "message_id": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": final_text}]
            },
            "metadata": {}
        },
        "id": 1
    }
    console.print(f"Calling remote agent: [bold yellow]{agent_name.capitalize()}[/bold yellow] with payload: [italic]{payload[:50]}...[/italic]")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(agent_url, json=rpc_payload, timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return f"Agent {agent_name} returned error: {json.dumps(data['error'])}"
                
                result = data.get("result", {})
                history = result.get("history", [])
                
                response_text = "No text output found."
                for item in reversed(history):
                    if item.get("role") in ["agent", "model"] and "parts" in item:
                        parts = item["parts"]
                        text_parts = [p["text"] for p in parts if "text" in p]
                        if text_parts:
                            response_text = "\n".join(text_parts)
                            break
                
                console.print(f"Remote agent [bold green]{agent_name.capitalize()}[/bold green] response received.")
                return response_text
            else:
                return f"Error calling agent {agent_name}: HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error calling agent {agent_name}: {str(e)}"

def register_to_rendezvous(agent_card_path: str):
    """
    Register an agent to the rendezvous agent and start a background heartbeat thread.
    
    Args:
        agent_card_path: Absolute path to the agent.json file.
        
    """
    if not os.path.exists(agent_card_path):
        console.print(f"[bold red]Error:[/bold red] Agent card not found at {agent_card_path}")
        return

    with open(agent_card_path, 'r') as f:
        agent_card = json.load(f)

    agent_id = agent_card.get('name')
    if not agent_id:
        console.print("[bold red]Error:[/bold red] Agent card must have a 'name' field.")
        return

    # Add agent_id for the registry if not present
    agent_card['agent_id'] = agent_id

    # Initial registration (Synchronous to ensure it happens before the server starts)
    try:
        with httpx.Client() as client:
            resp = client.post(f"{RENDEZVOUS_AGENT_URL}/register", json=agent_card, timeout=10.0)
            if resp.status_code == 200:
                print(f"****** Agent {agent_id} registered successfully. ******")
            else:
                print(f"Agent {agent_id} registration failed: {resp.status_code}")
    except Exception as e:
        print(f"Agent {agent_id} registration error: {e}")

    def run_heartbeat():
        # Wait a bit before starting heartbeats
        time.sleep(HEARTBEAT_INTERVAL)
        while True:
            try:
                with httpx.Client() as client:
                    resp = client.post(f"{RENDEZVOUS_AGENT_URL}/heartbeat", json={"agent_id": agent_id}, timeout=10.0)
                    if resp.status_code != 200:
                        # Re-register if heartbeat fails
                        client.post(f"{RENDEZVOUS_AGENT_URL}/register", json=agent_card, timeout=10.0)
            except Exception as e:
                logger.error(f"Heartbeat error for {agent_id}: {e}")
            time.sleep(HEARTBEAT_INTERVAL)

    thread = threading.Thread(target=run_heartbeat, daemon=True)
    thread.start()
    console.print(f"***** Heartbeat thread started for [bold cyan]{agent_id}[/bold cyan].*****")
