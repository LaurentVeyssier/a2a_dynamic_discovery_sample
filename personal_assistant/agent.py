from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.models import Gemini
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.adk.*")
from rich.console import Console
console = Console()
from dotenv import load_dotenv
import sys
import os

load_dotenv()

# Add parent directory to sys.path to allow importing discovery_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.discovery_tools import get_discovery_tools

# Instantiate tools with agent identity
discovery_agent_tool, handshake_tool, call_remote_agent_tool = get_discovery_tools("personal_assistant")

# Tool to provide passport data (mocked)
def get_passport() -> str:
    """Return the user's passport number (mocked)."""
    console.print("FUNC get_passport called by PERSONAL ASSISTANT AGENT", style="bold yellow")
    return "PA-123456789"

# Define the retry configuration
retry_config = types.HttpRetryOptions(
    attempts=3,          # Max number of retries
    initial_delay=2,     # Initial wait in seconds
    exp_base=2,          # Exponential multiplier (2s, 4s, 8s...)
    http_status_codes=[429, 500, 503]
)

root_agent = Agent(
    model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
    name="personal_assistant",
    description="Personal assistant that helps the user with their travel needs.",
    instruction=(
        "You are a personal assistant. Your role is to help the user with their requests.\n"
        "1. If you need a specific capability you don't have, use `discovery_agent_tool` with relevant keywords to find an appropriate agent.\n"
        "2. Once you find an agent, use `handshake_tool` with the agent's name to verify it's up and retrieve its capabilities.\n"
        "3. If the handshake is successful, use `call_remote_agent_tool` to delegate the task to that agent.\n"
        "4. When asked for passport information, call the `get_passport` tool.\n"
        "If asked unrelated questions, politely refuse."
    ),
    sub_agents=[], # No static sub-agents anymore
    tools=[get_passport, discovery_agent_tool, handshake_tool, call_remote_agent_tool],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
