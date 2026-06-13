import asyncio
import os
import json
import uuid
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from ai_tutor_agent.agent import root_agent
from ai_tutor_agent.utils.db_manager import db_manager
from google.adk.sessions import DatabaseSessionService
from google.genai import types

load_dotenv("ai_tutor_agent/.env", override=True)

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai_tutor.db'))
db_url = os.getenv("DATABASE_URI", f"sqlite:///{db_path}")
if db_url.startswith("sqlite:///"):
    adk_db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    adk_db_url = db_url

session_service = DatabaseSessionService(db_url=adk_db_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await session_service.init_db()
    except AttributeError:
        pass
    yield

app = FastAPI(title="AI Tutor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== MODELS ========
class LoginRequest(BaseModel):
    user_id: str

class SignupRequest(BaseModel):
    user_id: str
    name: str

class OnboardingStartRequest(BaseModel):
    user_id: str

class OnboardingChatRequest(BaseModel):
    user_id: str
    answer: str
    history: list[dict] = []

class CreatePathRequest(BaseModel):
    user_id: str
    session_id: str
    subject: str
    title: str
    syllabus: str

class ModelSettingRequest(BaseModel):
    mode: str

class QuizStartRequest(BaseModel):
    user_id: str
    session_id: str
    module_name: Optional[str] = None

class QuizAnswerRequest(BaseModel):
    user_id: str
    session_id: str
    history: list
    answer: str
    module_name: Optional[str] = None

# ======== AUTH ENDPOINTS ========

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = db_manager.get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/auth/signup")
async def signup(req: SignupRequest):
    result = db_manager.create_user(req.user_id, req.name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Signup failed"))
    return {"user_id": req.user_id, "name": req.name}

@app.post("/api/auth/guest")
async def guest_login():
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    db_manager.create_user(guest_id, "Guest User")
    return {"user_id": guest_id, "name": "Guest User"}

# ======== PATHS ENDPOINTS ========

@app.get("/api/paths")
async def get_paths(user_id: str):
    return db_manager.get_learning_paths(user_id)

@app.get("/api/paths/{session_id}")
async def get_path_details(session_id: str, user_id: str):
    paths = db_manager.get_learning_paths(user_id)
    path = next((p for p in paths if p['session_id'] == session_id), None)
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
    
    profile = db_manager.get_student_profile(user_id, path['subject'])
    
    syllabus_json = {}
    if path.get('syllabus'):
        try:
            syllabus_json = json.loads(path['syllabus'])
        except:
            pass

    return {
        "path": path,
        "profile": profile,
        "syllabus": syllabus_json
    }

@app.post("/api/paths/onboarding/start")
async def onboarding_start(req: OnboardingStartRequest):
    return {
        "question": "Hello! I am your AI Tutor. What subject would you like to learn today?",
        "options": ["Python Programming", "Web Development", "iOS Development", "Data Science", "System Design", "Machine Learning"]
    }

from fastapi_app.syllabus_engine import handle_onboarding_chat

@app.post("/api/paths/onboarding/chat")
async def onboarding_chat(req: OnboardingChatRequest):
    result = handle_onboarding_chat(req.history, req.answer)
    return result

@app.post("/api/paths/create")
async def create_path(req: CreatePathRequest):
    success = db_manager.create_learning_path(req.user_id, req.session_id, req.subject, req.title)
    if success:
        db_manager.update_learning_path_details(req.session_id, req.syllabus)
        return {"success": True}
    raise HTTPException(status_code=500, detail="Failed to create path")

# ======== QUIZ ENDPOINTS ========

from fastapi_app.quiz_engine import generate_first_question, evaluate_and_generate_next

@app.get("/api/quiz/pending")
async def quiz_pending(session_id: str, user_id: str):
    """Check if a quiz is pending for this session (used on page refresh/reconnect)."""
    pending_module = db_manager.get_quiz_pending(session_id)
    if pending_module:
        return {"pending": True, "module_name": pending_module}
    return {"pending": False, "module_name": None}

@app.post("/api/quiz/start")
async def quiz_start(req: QuizStartRequest):
    paths = db_manager.get_learning_paths(req.user_id)
    path = next((p for p in paths if p['session_id'] == req.session_id), None)
    if not path or not path.get('syllabus'):
        raise HTTPException(status_code=400, detail="Syllabus not found")
    
    # Set quiz as pending in DB (server-side enforcement)
    if req.module_name:
        db_manager.set_quiz_pending(req.session_id, req.module_name)
    
    question = generate_first_question(path['syllabus'], req.module_name)
    return question

@app.post("/api/quiz/answer")
async def quiz_answer(req: QuizAnswerRequest):
    paths = db_manager.get_learning_paths(req.user_id)
    path = next((p for p in paths if p['session_id'] == req.session_id), None)
    if not path or not path.get('syllabus'):
        raise HTTPException(status_code=400, detail="Syllabus not found")
        
    result = evaluate_and_generate_next(path['syllabus'], req.history, req.answer, req.module_name)
    if result.get("status") == "complete":
        try:
            syllabus_json = json.loads(path['syllabus'])
            syllabus_updated = False
            
            if isinstance(syllabus_json, dict) and "syllabus" in syllabus_json:
                syllabus_list = syllabus_json["syllabus"]
            elif isinstance(syllabus_json, dict) and "modules" in syllabus_json:
                syllabus_list = syllabus_json["modules"]
            else:
                syllabus_list = syllabus_json if isinstance(syllabus_json, list) else []
                
            # 1. ALWAYS mark module as completed (pass or fail, student advances)
            # 2. Find insertion point: right after the completed module/topic's parent module
            insert_idx = len(syllabus_list)  # default: append at end
            if req.module_name:
                for i, m in enumerate(syllabus_list):
                    m_title = m.get("title", m.get("module", ""))
                    topics = m.get("topics", [])
                    
                    # Check if it matches the module title OR any topic inside it
                    match_found = False
                    if req.module_name.lower() in m_title.lower() or m_title.lower() in req.module_name.lower():
                        match_found = True
                    else:
                        for t in topics:
                            if req.module_name.lower() in t.lower() or t.lower() in req.module_name.lower():
                                match_found = True
                                break
                                
                    if match_found:
                        # Add topic to completed_topics mapping
                        if "completed_topics" not in m:
                            m["completed_topics"] = []
                        if req.module_name not in m["completed_topics"]:
                            m["completed_topics"].append(req.module_name)
                            syllabus_updated = True
                            
                        # We don't mark the whole module as completed unless they finished the whole module,
                        # but for now, the user requested advancing to next topic, so we just set insert_idx
                        # to insert remedials right after this module.
                        insert_idx = i + 1
                        break
            
            # 3. Add a remedial topic for EACH wrong answer (per-question granularity)
            wrong_topics = result.get("final_review", {}).get("wrong_topics", [])
            remedials_added = 0
            for topic in wrong_topics:
                remedial_module = {
                    "module": f"Remedial: {topic}",
                    "title": f"Remedial: {topic}",
                    "status": "pending",
                    "subtopics": [f"Review: {topic}", "Practice exercises"],
                    "topics": [f"Review: {topic}", "Practice exercises"]
                }
                syllabus_list.insert(insert_idx + remedials_added, remedial_module)
                remedials_added += 1
                syllabus_updated = True
            
            # 4. Fallback: if LLM returned needs_remedial but no wrong_topics list
            if not wrong_topics and result.get("final_review", {}).get("needs_remedial"):
                remedial_topic = result["final_review"].get("remedial_topic", "Review")
                syllabus_list.insert(insert_idx, {
                    "module": f"Remedial: {remedial_topic}",
                    "title": f"Remedial: {remedial_topic}",
                    "status": "pending",
                    "subtopics": [f"Review: {remedial_topic}", "Practice exercises"],
                    "topics": [f"Review: {remedial_topic}", "Practice exercises"]
                })
                syllabus_updated = True
            
            if syllabus_updated:
                # Re-wrap in original structure
                if isinstance(syllabus_json, dict) and "syllabus" in syllabus_json:
                    syllabus_json["syllabus"] = syllabus_list
                elif isinstance(syllabus_json, dict) and "modules" in syllabus_json:
                    syllabus_json["modules"] = syllabus_list
                else:
                    syllabus_json = syllabus_list
                    
                new_syllabus_str = json.dumps(syllabus_json)
                db_manager.update_learning_path_details(req.session_id, new_syllabus_str)
                if result.get("final_review"):
                    result["final_review"]["syllabus_updated"] = True
            
            # 5. Clear the quiz_pending flag — student can now chat again
            db_manager.clear_quiz_pending(req.session_id)
                    
        except Exception as e:
            print("Error updating syllabus status:", e)
            # Still clear quiz pending even on error to avoid permanent lock
            db_manager.clear_quiz_pending(req.session_id)
            
    return result

# ======== CHAT ENDPOINTS ========

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str, user_id: str):
    return db_manager.get_chat_history(user_id, session_id=session_id)

@app.post("/api/chat/settings/model")
async def update_model_settings(req: ModelSettingRequest):
    # Ideally update environment variables or llm_config globally
    return {"status": "updated", "mode": req.mode}

# ======== WEBSOCKET ========

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, user_id: str):
    await websocket.accept()
    
    # Ensure session exists in ADK
    session = await session_service.get_session(app_name="ai_tutor", user_id=user_id, session_id=session_id)
    if not session:
        await session_service.create_session(
            app_name="ai_tutor", 
            user_id=user_id, 
            session_id=session_id, 
            state={"current_user_id": user_id, "session_id": session_id, "authenticated": True}
        )

    from google.adk.runners import Runner
    runner = Runner(app_name="ai_tutor", agent=root_agent, session_service=session_service)

    # Inject Syllabus Context Logic
    paths = db_manager.get_learning_paths(user_id)
    current_path = next((p for p in paths if p['session_id'] == session_id), None)
    context_injected = False

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            prompt = payload.get("prompt", "")

            hidden = payload.get("hidden", False)

            if not prompt:
                continue

            # SERVER-SIDE QUIZ ENFORCEMENT: Block all non-hidden messages while quiz is pending
            if not hidden:
                pending_module = db_manager.get_quiz_pending(session_id)
                if pending_module:
                    await websocket.send_json({
                        "type": "quiz_required",
                        "module": pending_module,
                        "content": f"You must complete the quiz for '{pending_module}' before continuing."
                    })
                    await websocket.send_json({"type": "done"})
                    continue

            # Log user query if not hidden
            if not hidden:
                db_manager.log_interaction(session_id, user_id, "user", prompt, "")

            # Context injection for the first message in session
            final_prompt = prompt
            if not context_injected and current_path and current_path.get('syllabus'):
                final_prompt = f"[System: Active Syllabus context:\n{current_path['syllabus']}]\n\n{prompt}"
                context_injected = True

            message = types.Content(role="user", parts=[types.Part(text=final_prompt)])
            full_response = ""
            current_agent = "ai_tutor"

            try:
                async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
                    # Check for tool calls / routing to update status pills
                    func_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else []
                    if func_calls:
                        for call in func_calls:
                            if call.name == "transfer_to_agent":
                                agent_name = call.args.get("agent_name", "specialist") if hasattr(call, 'args') and isinstance(call.args, dict) else "specialist"
                                display_name = agent_name.replace("_", " ").title()
                                await websocket.send_json({"type": "status", "content": f"Consulting {display_name}..."})
                            elif call.name == "trigger_topic_quiz":
                                module_name = "Unknown Topic"
                                if hasattr(call, 'args') and isinstance(call.args, dict):
                                    module_name = call.args.get("topic_name", call.args.get("module_name", "Unknown Topic"))
                                # Set quiz pending in DB — this blocks future chat messages
                                db_manager.set_quiz_pending(session_id, module_name)
                                await websocket.send_json({"type": "status", "content": f"Preparing Mandatory Quiz for {module_name}..."})
                                await websocket.send_json({"type": "trigger_quiz", "module": module_name})
                            else:
                                await websocket.send_json({"type": "status", "content": f"Running {call.name}..."})
                    
                    if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                full_response += part.text
                                await websocket.send_json({
                                    "type": "chunk", 
                                    "content": part.text,
                                    "author": event.author
                                })
                                current_agent = event.author
            except Exception as e:
                await websocket.send_json({"type": "chunk", "content": f"\n\nError: {str(e)}", "author": "system"})

            await websocket.send_json({"type": "done"})
            
            # Log final response
            db_manager.log_interaction(session_id, user_id, current_agent, "", full_response)

    except WebSocketDisconnect:
        pass

# Mount frontend
app.mount("/app", StaticFiles(directory="frontend/dist", html=True), name="frontend")

@app.get("/")
async def root():
    return RedirectResponse(url="/app/index.html")
