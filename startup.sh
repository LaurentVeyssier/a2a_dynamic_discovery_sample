#!/bin/bash
# for Azure Web App
set -e   # if part of the script fails → script exits immediately
python3 run_agents.py &
exec python3 frontend_app.py
