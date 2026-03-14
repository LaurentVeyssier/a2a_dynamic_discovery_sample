import sys
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.adk.*")
from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.models import Gemini
from dotenv import load_dotenv
# Add parent directory to sys.path to allow importing discovery_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.discovery_tools import get_discovery_tools

# Instantiate tools with agent identity
discovery_agent_tool, handshake_tool, call_remote_agent_tool = get_discovery_tools("travel_agent")

load_dotenv()

# Define the retry configuration
retry_config = types.HttpRetryOptions(
    attempts=3,          # Max number of retries
    initial_delay=2,     # Initial wait in seconds
    exp_base=2,          # Exponential multiplier (2s, 4s, 8s...)
    http_status_codes=[429, 500, 503]
)

# Travel Agent that coordinates between requester (personal assistant) and airline
root_agent = Agent(
    model=Gemini(model=os.getenv("MODEL_NAME", "gemini-2.5-flash"), retry_options=retry_config),
    name="travel_agent",
    description="Travel agent that books flights by coordinating with an airline and the user's personal assistant.",
    instruction=(
        "You are a travel agent. Your goal is to manage the travelling request for the user.\n"
        "1. If you need a specific capability or an information you don't have, use `discovery_agent_tool` with relevant keywords to find an appropriate agent.\n"
        "2. Once you find an agent, use `handshake_tool` with the agent's name to verify it's up and retrieve its capabilities.\n"
        "3. If the handshake is successful, use `call_remote_agent_tool` to delegate the task to that agent.\n\n"
        "IMPORTANT: You are the ORCHESTRATOR. You must maintain the STATE of the request.\n"
        "If you need to call an agent a second time (e.g., providing missing info like a passport), you MUST pass the previous context/task details in the `task_context` argument.\n"
        "Example: call_remote_agent_tool('airline', 'Here is the passport', task_context='Original Task: Book flight to Tokyo on 2026-06-01')\n"
        "If the user hasn't provided passport_number yet, set it to null. Never ask the user for information. Use discovery_agent_tool to find who can provide it.\n\n"
        "You MUST handle the complete workflow within a single response turn; you may call sub-agents multiple times before replying.\n"
        "Only the final confirmation of the executed request should be returned."
    ),
    sub_agents=[],
    tools=[ discovery_agent_tool, handshake_tool, call_remote_agent_tool],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
