import asyncio
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from ai_tutor_agent.agent import root_agent
from ai_tutor_agent.utils.db_manager import db_manager
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.session import Session
from google.genai import types
from typing import Optional

load_dotenv("ai_tutor_agent/.env", override=True)

# Use ADK's native DatabaseSessionService for reliable async persistence
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai_tutor.db'))
db_url = os.getenv("DATABASE_URI", f"sqlite:///{db_path}")
if db_url.startswith("sqlite:///"):
    adk_db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    adk_db_url = db_url

session_service = DatabaseSessionService(db_url=adk_db_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    try:
        await session_service.init_db()  # If ADK supports it, or let db_manager handle sync init
    except AttributeError:
        pass
    yield
    # Cleanup DB connection on shutdown
    pass

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI Tutor Streaming API", lifespan=lifespan)

# Mount the static frontend. html=True automatically serves index.html at root "/"
app.mount("/app", StaticFiles(directory="fastapi_app/frontend", html=True), name="frontend")

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/app/index.html")

@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    """Streaming endpoint for AI Tutor."""
    data = await request.json()
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    prompt = data.get("prompt")
    
    if not user_id or not session_id or not prompt:
        return {"error": "Missing parameters"}

    # Ensure session exists in the DB service wrapper
    session = await session_service.get_session(app_name="ai_tutor", user_id=user_id, session_id=session_id)
    if not session:
        await session_service.create_session(
            app_name="ai_tutor", 
            user_id=user_id, 
            session_id=session_id, 
            state={
                "current_user_id": user_id,
                "session_id": session_id,
                "authenticated": True
            }
        )
        
    from google.adk.runners import Runner
    
    # We must construct a native Runner inside the endpoint
    # to yield chunks to the frontend.
    runner = Runner(
        app_name="ai_tutor",
        agent=root_agent,
        session_service=session_service
    )
    
    async def generate():
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        
        # Async iterate over the streaming runner events
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            # Parse chunks and yield as Server-Sent Events (SSE)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        # Yield SSE chunk
                        chunk_data = json.dumps({"type": "chunk", "content": part.text, "author": event.author})
                        yield f"data: {chunk_data}\n\n"
        
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
