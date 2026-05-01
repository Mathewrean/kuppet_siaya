#!/bin/bash
# Start the application with Uvicorn ASGI server for concurrent request handling

# Kill any existing uvicorn processes
pkill -f "uvicorn kuppetsiaya.asgi" 2>/dev/null || true

# Start Uvicorn with multiple workers for concurrent requests
uvicorn kuppetsiaya.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --http h11 \
    --lifespan on