#!/bin/bash
# for Azure Web App
# Activate the virtual environment that uv created
source /antenv/bin/activate
# start up command
set -e   # if part of the script fails → script exits immediately
python3 run_agents.py &
exec python3 frontend_app.py
