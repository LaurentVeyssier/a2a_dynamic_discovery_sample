import asyncio
import json
import os
import uuid
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
event_history = []
event_counter = 0
history_lock = asyncio.Lock()
subscribers = set()

# Constants
PA_AGENT_URL = os.getenv("PA_AGENT_URL", "http://127.0.0.1:9002")

class ChatMessage(BaseModel):
    message: str

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(msg: ChatMessage):
    """
    Proxy chat message to the Personal Assistant agent.
    Forwards user messages to the PA agent endpoint: Port
    """
    rpc_payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "message_id": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": msg.message}]
            },
            "metadata": {}
        },
        "id": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(PA_AGENT_URL, json=rpc_payload, timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return {"error": data["error"]}
                
                result = data.get("result", {})
                history = result.get("history", [])
                
                response_text = "No response from agent."
                for item in reversed(history):
                    if item.get("role") in ["agent", "model"] and "parts" in item:
                        parts = item["parts"]
                        text_parts = [p["text"] for p in parts if "text" in p]
                        if text_parts:
                            response_text = "\n".join(text_parts)
                            break
                return {"response": response_text}
            else:
                return {"error": f"Agent error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

@app.post("/api/trace")
async def trace(event: dict):
    """
    Receives event reports from agents and broadcasts them via SSE.
    Receive event logs from agents and put them in the SSE queue.
    """
    global event_counter
    async with history_lock:
        event_counter += 1
        event['sequence'] = event_counter
        event_history.append(event)
        if len(event_history) > 100:
            event_history.pop(0)
            
    logger.info(f"Received event {event_counter}: {event.get('type')} from {event.get('agent')}")
    
    # Broadcast to all active subscribers
    for q in list(subscribers):
        try:
            q.put_nowait(event)
        except Exception:
            pass
            
    return {"status": "ok"}

@app.get("/api/events")
async def events(request: Request):
    """
    This is the SSE (Server-Sent Events) endpoint for the frontend.
    SSE endpoint for the frontend to listen for events.
    """
    async def event_generator():
        queue = asyncio.Queue()
        subscribers.add(queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                try:
                    event = await queue.get()
                    yield {
                        "data": json.dumps(event)
                    }
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in event generator: {e}")
                    yield {
                        "data": json.dumps({"type": "error", "message": str(e)})
                    }
        finally:
            subscribers.remove(queue)

    return EventSourceResponse(event_generator())

# Serve static files (after API routes)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("frontend_app:app", host="127.0.0.1", port=8000)
