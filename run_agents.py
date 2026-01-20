import subprocess
import shutil
import time
import sys
import os
from rich.console import Console

console = Console()

AGENTS = [
    {"name": "airline_agent", "path": "airline_agent", "port": 9000},
    {"name": "travel_agent", "path": "travel_agent", "port": 9001},
    {"name": "personal_assistant", "path": "personal_assistant", "port": 9002},
]


def get_uvicorn_command(module_path: str, port: int):
    # 1. Check if 'uv' is installed on the system
    uv_path = shutil.which("uv")
    
    if uv_path:
        # If uv exists, use your preferred high-speed command
        return [
            "uv", "run", "uvicorn", module_path,
            "--host", "0.0.0.0",
            "--port", str(port),
        ]
    else:
        # Fallback for Koyeb/Render: use the standard python interpreter
        # -m uvicorn ensures it uses the version installed in requirements.txt
        return [
            sys.executable, "-m", "uvicorn", module_path,
            "--host", "0.0.0.0",
            "--port", str(port),
            "--workers", "1"  # Crucial for staying under 512MB RAM
        ]

def run_agents():
    processes = []
    
    console.print("[bold blue]Starting all agents...[/bold blue]")
    
    for agent in AGENTS:
        # Construct the uvicorn command
        # Format: uvicorn <folder>.<file_basename>:a2a_app

        # Convert file paths (agents/travel_agent) to python imports (agents.travel_agent)
        clean_path = agent['path'].replace("/", ".").replace("\\", ".")
        module_path = f"{clean_path}.agent:a2a_app"
        cmd = get_uvicorn_command(module_path, agent["port"])
        
        console.print(f"Starting [bold cyan]{agent['name']}[/bold cyan] on port {agent['port']}...")
        
        # Prepare environment with agent name
        agent_env = os.environ.copy()
        agent_env["AGENT_NAME"] = agent["name"].replace("_", " ").upper()
        
        # Start the process. Using a separate shell on Windows to see output if needed, 
        # but here we'll just pipe it to keep it clean.
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=agent_env
        )
        processes.append((agent["name"], process))
        
        # Short sleep to let the server start and register
        time.sleep(0.5)

    console.print("\n[bold green]All agents are running![/bold green]")
    console.print("Press Ctrl+C to stop all agents.\n")

    try:
        while True:
            for name, proc in processes:
                # Read output non-blockingly (simple version)
                line = proc.stdout.readline()
                if line:
                    console.print(f"[[bold]{name}[/bold]] {line.strip()}")
                
                if proc.poll() is not None:
                    console.print(f"[bold red]Process {name} exited with code {proc.returncode}[/bold red]")
                    return
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopping all agents...[/bold yellow]")
        for name, proc in processes:
            proc.terminate()
            console.print(f"Stopped {name}.")

if __name__ == "__main__":
    run_agents()
