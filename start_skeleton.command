#!/bin/bash
# Double-click me: serves the Fly Lab on http://localhost:8200 and opens it in your browser.
# It also runs the "Ask Muse" panel (tools/server.py). Muse needs your Meta API key in .env
# (META_API_KEY=...) in this folder or in "Fly Brain/.env"; without it the lab still works and Muse says it is offline.
# Close this Terminal window (or press Ctrl+C) to stop the server.
cd "$(dirname "$0")"
PORT=8200
pid=$(lsof -ti tcp:$PORT 2>/dev/null)
if [ -n "$pid" ]; then echo "Freeing port $PORT (process $pid)"; kill $pid 2>/dev/null; sleep 1; fi
python3 -c "import openai" 2>/dev/null || { echo "Installing the 'openai' package for Muse (one time)..."; python3 -m pip install --user --quiet openai; }
( sleep 1.5; open "http://localhost:$PORT/" ) &
FLYLAB_PORT=$PORT exec python3 tools/server.py
