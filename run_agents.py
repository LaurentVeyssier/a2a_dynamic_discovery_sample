import subprocess
import shutil
import time
import sys
import os
from rich.console import Console

# Add current directory to path so we can import tools
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from tools.discovery_tools import register_to_rendezvous

console = Console()

AGENTS_DIRS = ["airline_agent", "travel_agent", "personal_assistant"]

def run_agents():
    # 1. Register Agents
    console.print("[bold blue]Registering agents...[/bold blue]")
    for agent_dir in AGENTS_DIRS:
        card_path = os.path.abspath(os.path.join(agent_dir, "agent.json"))
        if os.path.exists(card_path):
            console.print(f"Registering {agent_dir}...")
            # Note: register_to_rendezvous starts a daemon thread for heartbeat, 
            # which will stay alive as long as this main script is running.
            register_to_rendezvous(card_path)
        else:
            console.print(f"[bold red]Warning: No agent.json found for {agent_dir}[/bold red]")

    # 2. Start ADK Server
    # Check for 'uv'
    uv_path = shutil.which("uv")
    
    # We pass "." to scan the current directory for agents
    if uv_path:
        console.print("[bold green]uv detected. Using 'uv run adk'[/bold green]")
        cmd = [
            "uv", "run", "adk", "api_server", ".", "--a2a", "--port", "9000", "--log_level", "warning"
        ]
    else:
        console.print("[bold yellow]uv not found. Using 'adk' directly[/bold yellow]")
        cmd = [
            "adk", "api_server", ".", "--a2a", "--port", "9000", "--log_level", "warning"
        ]

    console.print(f"\n[bold blue]Starting agents with command:[/bold blue] {' '.join(cmd)}")

    # Prepare environment
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        
        console.print("[bold green]ADK Server running on port 9000...[/bold green]")
        console.print("Access agents at http://127.0.0.1:9000/a2a/<agent_name>")
        console.print("Press Ctrl+C to stop.\n")

        while True:
            # Read output non-blockingly
            line = process.stdout.readline()
            if line:
                console.print(f"[ADK] {line.strip()}")
            
            if process.poll() is not None:
                console.print(f"[bold red]Process exited with code {process.returncode}[/bold red]")
                break
            time.sleep(0.01)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopping ADK server...[/bold yellow]")
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            console.print("Stopped.")
    except Exception as e:
        console.print(f"[bold red]Error running agents: {e}[/bold red]")
        if 'process' in locals():
            process.kill()

if __name__ == "__main__":
    run_agents()
