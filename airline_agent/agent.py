import sys
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.adk.*")
from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.tools.example_tool import ExampleTool
from rich.console import Console
console = Console()
from dotenv import load_dotenv
load_dotenv()
# Add parent directory to sys.path to allow importing discovery_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.discovery_tools import get_discovery_tools

# Instantiate tools with agent identity
discovery_agent_tool, handshake_tool, call_remote_agent_tool = get_discovery_tools("airline_agent")

# Tool: concrete booking endpoint with explicit arguments
def book_flight(destination: str, date: str, passport_number: str | None = None) -> str:
    """Book a flight. Requires destination, date, and passport_number."""
    console.print("FUNC book_flight called by AIRLINE AGENT - destination: ", destination, "date: ", date, "passport_number: ", passport_number, style="bold yellow")
    if not destination:
        console.print("FUNC book_flight returning: ", "error: destination is required", style="bold red")
        return "error: destination is required"
    if not date:
        console.print("FUNC book_flight returning: ", "error: date is required", style="bold red")
        return "error: date is required"
    if not passport_number:
        console.print("FUNC book_flight returning: ", "error: passport_number is required", style="bold red")
        return "error: passport_number is required"
    console.print("FUNC book_flight returning: ", f"Booking confirmed to {destination} on {date} for passport {passport_number}", style="bold green")
    return f"Booking confirmed to {destination} on {date} for passport {passport_number}"


example_tool = ExampleTool([
    {
        "input": {"role":"user","parts":[{"text":"Book to Dublin on 2026-01-25"}]},
        "output": [
            {"role":"model","parts":[{"text":"error: passport_number is required"}]},
        ],
    },
    {
        "input": {"role":"user","parts":[{"text":"Book to Paris on 2026-05-10 with passport PA-123"}]},
        "output": [
            {"role":"model","parts":[{"text":"Booking confirmed to Paris on 2026-05-10 for passport PA-123"}]},
        ],
    },
])

root_agent = Agent(
    model="gemini-2.0-flash",
    name="airline_agent",
    description="Airline company agent that books flights and requires passport details to confirm.",
    instruction=(
        "You are an airline booking agent.\n"
        "1. Always call the `book_flight` tool with arguments destination (str), date (str), and passport_number (str or null).\n"
        "2. If you need to find other agents, use `discovery_agent_tool` and `handshake_tool`.\n"
        "3. Return only the tool’s output string. Do not include any meta text.\n"
        "If booking succeeds, return the confirmation string verbatim."
    ),
    tools=[book_flight, example_tool, discovery_agent_tool, handshake_tool, call_remote_agent_tool],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
