import streamlit as st
import streamlit.components.v1 as components
import re
import sys
import os
import uuid
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from dotenv import load_dotenv

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv("ai_tutor_agent/.env", override=True)

from ai_tutor_agent.utils.db_manager import db_manager
from ai_tutor_agent.agent import root_agent

st.set_page_config(page_title="AI Tutor Platform", page_icon="🎓", layout="wide")

def render_message_with_mermaid(text: str):
    import base64
    parts = re.split(r'```mermaid\n(.*?)```', text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part.strip():
                st.markdown(part)
        else:
            try:
                # Convert mermaid string to base64 for server-side image rendering
                b64 = base64.b64encode(part.encode('utf-8')).decode('utf-8')
                st.image(f"https://mermaid.ink/img/{b64}")
            except Exception as e:
                # Fallback to code block if it fails
                st.code(part, language="mermaid")

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "sidebar_view" not in st.session_state:
    st.session_state.sidebar_view = "list" # 'list' or 'detail'

@st.cache_resource
def get_runner():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ai_tutor.db'))
    db_url = os.getenv("DATABASE_URI", f"sqlite:///{db_path}")
    if db_url.startswith("sqlite:///"):
        adk_db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    else:
        adk_db_url = db_url

    session_service = DatabaseSessionService(db_url=adk_db_url)
    runner = Runner(
        app_name="ai_tutor",
        agent=root_agent,
        session_service=session_service
    )
    return runner

def login_page():
    st.title("🎓 AI Tutor Login")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Guest Access"])
    
    with tab1:
        with st.form("login_form"):
            user_id = st.text_input("User ID")
            submit = st.form_submit_button("Login")
            
            if submit and user_id:
                user = db_manager.get_user(user_id)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user["user_id"]
                    st.session_state.username = user["name"]
                    st.session_state.agent_notified = False  # Reset notification state
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("User ID not found.")
    
    with tab2:
        with st.form("signup_form"):
            new_user_id = st.text_input("Choose User ID")
            new_name = st.text_input("Your Name")
            submit = st.form_submit_button("Create Account")
            
            if submit and new_user_id and new_name:
                if db_manager.get_user(new_user_id):
                    st.error("User ID already exists.")
                else:
                    res = db_manager.create_user(new_user_id, new_name)
                    if res["success"]:
                        st.success("Account created! Please login.")
                    else:
                        st.error(f"Error: {res.get('error')}")
    
    with tab3:
        st.write("Continue as a guest to try out the platform.")
        if st.button("Continue as Guest"):
            guest_id = f"guest_{uuid.uuid4().hex[:6]}"
            res = db_manager.create_user(guest_id, "Guest User")
            if res["success"]:
                st.session_state.authenticated = True
                st.session_state.user_id = guest_id
                st.session_state.username = "Guest User"
                st.session_state.is_guest = True
                st.session_state.agent_notified = False  # Reset notification state
                st.rerun()

def get_onboarding_runner():
    from google.adk.runners import Runner
    from google.adk.sessions import DatabaseSessionService
    from ai_tutor_agent.subagents.onboarding_agent.agent import onboarding_agent
    import os
    if "wiz_runner" not in st.session_state:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ai_tutor.db'))
        db_url = os.getenv("DATABASE_URI", f"sqlite:///{db_path}")
        if db_url.startswith("sqlite:///"):
            adk_db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            adk_db_url = db_url

        session_service = DatabaseSessionService(db_url=adk_db_url)
        st.session_state.wiz_runner = Runner(
            app_name="ai_tutor_wizard",
            agent=onboarding_agent,
            session_service=session_service
        )
    return st.session_state.wiz_runner

@st.dialog("🎓 Start a New Subject")
def onboarding_wizard():
    import json
    import re
    import uuid
    import asyncio
    
    if "wiz_step" not in st.session_state:
        st.session_state.wiz_step = 0
        st.session_state.wiz_subject = ""
        st.session_state.wiz_level = "Beginner"
        st.session_state.wiz_state_json = None
        import uuid
        st.session_state.wiz_session_id = f"wiz_{uuid.uuid4().hex}"
        
        runner = get_onboarding_runner()
        import asyncio
        def get_or_create_loop():
            try:
                return asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
        loop = get_or_create_loop()
        loop.run_until_complete(
             runner.session_service.create_session(
                app_name="ai_tutor_wizard",
                user_id=st.session_state.user_id,
                session_id=st.session_state.wiz_session_id,
                state={}
            )
        )

    if st.session_state.wiz_step == 0:
        st.write("What would you like to learn today?")
        subject = st.text_input("Subject (e.g., Python, System Design, DSA)")
        level = st.selectbox("Your current experience level", ["Beginner", "Intermediate", "Advanced"])
        if st.button("Next"):
            if subject.strip():
                st.session_state.wiz_subject = subject
                st.session_state.wiz_level = level
                
                with st.spinner("Analyzing..."):
                    runner = get_onboarding_runner()
                    prompt = f"Student wants to learn: {subject}. Experience level: {level}."
                    
                    from google.genai import types
                    response_text = ""
                    for event in runner.run(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.wiz_session_id,
                        new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
                    ):
                        if getattr(event, "content", None) and getattr(event.content, "parts", None):
                            for p in event.content.parts:
                                if getattr(p, "text", None):
                                    response_text += p.text
                    
                    import json, re
                    match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if match:
                        try:
                            st.session_state.wiz_state_json = json.loads(match.group(0))
                            if st.session_state.wiz_state_json.get("status") == "complete":
                                st.session_state.wiz_step = 2
                            else:
                                st.session_state.wiz_step = 1
                        except:
                            st.error("Failed to parse AI response.")
                    else:
                        # Fallback if AI messes up
                        st.session_state.wiz_state_json = {"status": "complete", "syllabus": [{"module": "1. Introduction", "status": "pending", "subtopics": ["Getting Started"]}]}
                        st.session_state.wiz_step = 2
                st.rerun()
            else:
                st.error("Please enter a subject.")

    elif st.session_state.wiz_step == 1:
        state_data = st.session_state.wiz_state_json
        if state_data.get("status") == "asking":
            st.write("To personalize your syllabus, please answer these questions:")
            answers = {}
            for q in state_data.get("questions", []):
                if q.get("type") == "multiple_choice" and "options" in q:
                    answers[q["id"]] = st.radio(q["text"], q["options"], key=f"q_{q['id']}")
                else:
                    answers[q["id"]] = st.text_input(q["text"], key=f"q_{q['id']}")
                    
            if st.button("Submit Answers"):
                ans_str = json.dumps(answers)
                with st.spinner("Processing..."):
                    runner = get_onboarding_runner()
                    prompt = f"Student answers: {ans_str}"
                    
                    from google.genai import types
                    response_text = ""
                    for event in runner.run(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.wiz_session_id,
                        new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
                    ):
                        if getattr(event, "content", None) and getattr(event.content, "parts", None):
                            for p in event.content.parts:
                                if getattr(p, "text", None):
                                    response_text += p.text
                                    
                    import json, re
                    match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if match:
                        try:
                            new_state = json.loads(match.group(0))
                            st.session_state.wiz_state_json = new_state
                            if new_state.get("status") == "complete":
                                st.session_state.wiz_step = 2
                        except Exception as e:
                            st.error(f"Error parsing next step: {e}")
                st.rerun()
                
        elif state_data.get("status") == "complete":
             st.session_state.wiz_step = 2
             st.rerun()
             
    if st.session_state.wiz_step == 2:
        st.write("Generating your personalized syllabus...")
        with st.spinner("Finishing up..."):
            syllabus_data = st.session_state.wiz_state_json.get("syllabus", [])
            if not syllabus_data:
                syllabus_data = [{"module": "1. Introduction", "status": "pending", "subtopics": ["Getting Started"]}]
            
            syllabus_dict = {"syllabus": syllabus_data} if isinstance(syllabus_data, list) else syllabus_data
            
            # create path and details
            import uuid
            new_session_id = str(uuid.uuid4())
            title = st.session_state.wiz_subject.replace("_", " ").title()
            
            from ai_tutor_agent.utils.db_manager import db_manager
            db_manager.create_learning_path(
                user_id=st.session_state.user_id,
                session_id=new_session_id,
                subject=st.session_state.wiz_subject.lower(),
                title=title
            )
            
            import json
            db_manager.update_learning_path_details(new_session_id, json.dumps(syllabus_dict))
            db_manager.update_student_profile(st.session_state.user_id, st.session_state.wiz_subject.lower(), st.session_state.wiz_level)
            
            # Reset and redirect
            st.session_state.session_id = new_session_id
            st.session_state.messages = [{
                "role": "assistant",
                "content": f"Welcome! I've created your personalized syllabus for **{st.session_state.wiz_subject.title()}**. Take a look at the sidebar, and let me know when you're ready to start the first module!",
                "sender_name": "AI Tutor"
            }]
            st.session_state.agent_notified = True
            st.session_state.sidebar_view = 'detail'
            st.session_state.show_wizard = False
            
            # Clear wizard state
            for k in list(st.session_state.keys()):
                if k.startswith("wiz_"):
                    del st.session_state[k]
                    
            st.rerun()

def chat_page():
    runner = get_runner()
    
    import asyncio
    
    def get_or_create_loop():
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
            
    loop = get_or_create_loop()
    
    # 1. Identify Current Path from Session ID
    paths = db_manager.get_learning_paths(st.session_state.user_id)
    current_path = next((p for p in paths if p['session_id'] == st.session_state.session_id), None)
    
    # Ensure session exists in runner
    from google.adk.errors.session_not_found_error import SessionNotFoundError
    try:
        loop.run_until_complete(
            runner.session_service.get_session(
                app_name="ai_tutor",
                user_id=st.session_state.user_id,
                session_id=st.session_state.session_id
            )
        )
    except SessionNotFoundError:
        # Create session if it doesn't exist
        state_dict = {
            "authenticated": True,
            "current_user_id": st.session_state.user_id,
            f"user:{st.session_state.user_id}_name": st.session_state.username,
            "session_id": st.session_state.session_id 
        }
        loop.run_until_complete(
             runner.session_service.create_session(
                app_name="ai_tutor",
                user_id=st.session_state.user_id,
                session_id=st.session_state.session_id,
                state=state_dict
            )
        )
        st.session_state.agent_notified = False

    # 2. Load history from DB if message are empty (reloading/switching)
    is_new_session = False
    if not st.session_state.messages:
        # Pass session_id to get relevant history!
        history = db_manager.get_chat_history(st.session_state.user_id, session_id=st.session_state.session_id, limit=30)
        if history:
            for h in history:
                st.session_state.messages.append({"role": "user", "content": h["query"]})
                st.session_state.messages.append({"role": "assistant", "content": h["response"]})
        else:
            is_new_session = True

    # 3. Sidebar: Navigation (Learning Paths)
    # 3. Sidebar: Navigation (Learning Paths)
    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        if st.caption: st.caption(f"ID: {st.session_state.user_id}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        
        # --- MODEL SETTINGS ---
        st.markdown("### ⚙️ Settings")
        if "model_mode" not in st.session_state:
            st.session_state.model_mode = "Online (Gemini)"
            
        new_model_mode = st.radio("AI Engine", ["Online (Gemini)", "Local (Ollama)"], index=0 if st.session_state.model_mode == "Online (Gemini)" else 1)
        
        if new_model_mode != st.session_state.model_mode:
            st.session_state.model_mode = new_model_mode
            st.rerun()

        def update_agent_models(target_model):
            """Update model on root + all sub_agents."""
            from google.adk.models.lite_llm import LiteLlm
            if isinstance(target_model, str) and "/" in target_model:
                model_obj = LiteLlm(model=target_model)
            else:
                model_obj = target_model
            root_agent.model = model_obj
            # Update sub_agents (not tools anymore)
            for sub in getattr(root_agent, 'sub_agents', []):
                sub.model = model_obj

        if st.session_state.model_mode == "Local (Ollama)":
            local_model = "ollama/llama3.1"
            update_agent_models(local_model)
            st.caption(f"🦙 Local: `{local_model}`")
        else:
            if "GOOGLE_GEMINI_BASE_URL" in os.environ:
                del os.environ["GOOGLE_GEMINI_BASE_URL"]
            online_model = "gemini-2.5-flash"
            update_agent_models(online_model)
            st.caption(f"☁️ Online: `{online_model}`")
            
        st.divider()
        
        # --- VIEW LOGIC ---
        # Determine effective view mode
        # If we have a current path, we default to detail view unless explicitly back in list mode
        # Actually, let's strictly follow the state variable, but sync it on first load if needed
        
        show_detail = False
        if current_path and st.session_state.sidebar_view == 'detail':
            show_detail = True
            
        if show_detail:
            # === DETAIL VIEW (Active Path) ===
            if st.button("🔙 Back to Paths", use_container_width=True):
                # Just change the view, DO NOT reset the session
                st.session_state.sidebar_view = 'list'
                st.rerun()

            st.markdown(f"### 📂 {current_path['title']}")
            
            # Fetch Progress
            profile = db_manager.get_student_profile(st.session_state.user_id, subject=current_path['subject'])
            
            if profile:
                st.caption(f"**Subject:** {profile['subject'].upper()}")
                
                # Progress Bar
                level_str = profile['level'].lower()
                progress_val = 0.1 if 'beginner' in level_str else 0.5 if 'intermediate' in level_str else 0.9
                st.progress(progress_val)
                st.caption(f"Level: {profile['level'].title()}")
                
                # Detailed Syllabus Rendering
                st.divider()
                st.markdown("**🎓 Course Syllabus**")
                
                # PREFER Path-specific syllabus, fallback to Profile (legacy)
                path_syllabus_raw = current_path.get('syllabus')
                if path_syllabus_raw and path_syllabus_raw != '{}':
                     details_raw = path_syllabus_raw
                else:
                     details_raw = profile.get('details', '{}')
                try:
                    import json
                    # Helper for recursive parsing
                    def try_parse_json(c, d=3):
                        if d==0: return c
                        if isinstance(c, str):
                            try: return try_parse_json(json.loads(c), d-1)
                            except: return c
                        return c
                    
                    data = try_parse_json(details_raw)
                    syllabus_list = None
                    
                    if isinstance(data, dict) and "syllabus" in data:
                        syllabus_list = data["syllabus"]
                    elif isinstance(data, list):
                        syllabus_list = data
                        
                    if syllabus_list:
                         for item in syllabus_list:
                            if isinstance(item, dict):
                                module_name = item.get("module", "Module")
                                status = item.get("status", "pending").lower()
                                subtopics = item.get("subtopics", [])
                                
                                icon = "🔵"
                                if status == "completed": icon = "🟢"
                                elif status == "in_progress": icon = "🟡"
                                
                                with st.expander(f"{icon} {module_name}"):
                                    if subtopics:
                                        for sub in subtopics:
                                            st.markdown(f"- {sub}")
                                    else:
                                        st.caption("No details")
                            else:
                                st.write(f"• {item}")
                    else:
                        st.info("Syllabus generating...")
                        
                except Exception as e:
                    st.caption("Parsing progress details...")
            else:
                st.info("Initializing progress...")

        else:
            # === ROOT VIEW (List Paths) ===
            if st.button("➕ New Chat", use_container_width=True):
                st.session_state.show_wizard = True
                
            if st.session_state.get("show_wizard", False):
                onboarding_wizard()
                
            st.subheader("Learning Paths")
            
            if paths:
                for p in paths:
                    # Identify if this is the active path
                    is_active = p['session_id'] == st.session_state.session_id
                    
                    label = f"{'📂' if is_active else '📁'} {p['title']}"
                    
                    if st.button(label, key=p['id'], use_container_width=True, type="primary" if is_active else "secondary"):
                        # Only reload if it's a DIFFERENT session
                        if not is_active:
                            st.session_state.session_id = p['session_id']
                            st.session_state.messages = [] # Reload history
                            st.session_state.agent_notified = True
                        
                        # Always switch to Detail view
                        st.session_state.sidebar_view = 'detail'
                        st.rerun()
            else:
                st.info("Start chatting to create a path!")

    # 4. Auto-Login Notification
    if not st.session_state.get("agent_notified", False):
        try:
            if is_new_session and not current_path:
                # Add a local greeting instead of blocking the UI with a synchronous LLM generation
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"Welcome {st.session_state.username}! I am your AI Tutor. What would you like to learn today? (e.g., DSA, React, System Design)",
                    "sender_name": "AI Tutor"
                })
            st.session_state.agent_notified = True
        except Exception as e:
            st.error(f"Failed to notify agent of login: {e}")

    # 5. Main Chat Area
    st.title("AI Tutor Assistant" if not current_path else current_path['title'])
    
    # Welcome Message / Capabilities (Only for blank new chats)
    if not st.session_state.messages and not current_path:
        st.markdown("""
        ### 👋 Welcome to AI Tutor!
        I'm here to help you master technical subjects. 
        
        **Start by picking a topic:**
        - 🧩 **DSA**: Algorithms, Data Structures
        - 💻 **Development**: Web, Mobile, React, Python
        - 🏗️ **System Design**: Architecture, Cloud
        
        *Ask me anything to get started!*
        """)

    # Display messages
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        sender_name = msg.get("sender_name")
        
        # Determine display name and avatar
        if role == "user":
            display_name = sender_name or st.session_state.username or "Student"
            avatar = "👤"
        else:
            # Map internal agent names to friendly titles
            agent_mapping = {
                "root_agent": "AI Tutor",
                "dsa_tutor": "DSA Tutor",
                "dsa_solver": "DSA Solver",
                "code_generator": "Code Generator",
                "code_reviewer": "Code Reviewer",
                "developer_tutor": "Developer Tutor",
                "system_design_tutor": "System Design Tutor",
                "search_agent": "Search Agent",
                "account_agent": "Account Manager"
            }
            raw_name = sender_name or "AI Tutor"
            display_name = agent_mapping.get(raw_name, raw_name.replace("_", " ").title())
            avatar = "🤖"

        with st.chat_message(name=display_name, avatar=avatar):
            st.write(f"**{display_name}**")
            render_message_with_mermaid(content)

    if prompt := st.chat_input("Ask me anything about DSA, System Design, or Coding..."):
        # Add user message
        user_name = st.session_state.username or "Student"
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt, 
            "sender_name": user_name
        })
        with st.chat_message(user_name, avatar="👤"):
            st.write(f"**{user_name}**")
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("AI Tutor", avatar="🤖"):
             with st.status("Agent is analyzing request...", expanded=True) as status:
                try:
                    # Run agent via Runner
                    response_text = ""
                    last_author = "root_agent" 
                    turn_count = 0
                    llm_prompt = prompt
                    # Inject syllabus to ensure context, especially at start of session
                    if current_path and current_path.get('syllabus') and current_path.get('syllabus') != '{}':
                        if len(st.session_state.messages) <= 2 or len(prompt) < 30:
                            llm_prompt = f"[SYSTEM CONTEXT: The active syllabus for {current_path['subject']} is: {current_path['syllabus']}]\n\nUser Request: {prompt}"
                            
                    for event in runner.run(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                        new_message=types.Content(role="user", parts=[types.Part(text=llm_prompt)])
                    ):
                        turn_count += 1
                        if turn_count > 8:
                            status.write("🛑 Agent is looping. Forcing a stop to save resources.")
                            if not response_text:
                                response_text = "I apologize, but I got confused while routing your request. Could you rephrase it simply?"
                            break
                            
                        if getattr(event, 'author', None):
                            last_author = event.author
                            
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if getattr(part, 'function_call', None):
                                    fname = part.function_call.name
                                    if fname == 'transfer_to_agent':
                                        agent_name = ''
                                        try:
                                            agent_name = part.function_call.args.get('agent_name', '')
                                        except Exception:
                                            pass
                                        friendly = agent_name.replace('_', ' ').title()
                                        status.write(f"🔀 Routing to **{friendly}**...")
                                    elif 'learning_path' in fname or 'create_learning' in fname:
                                        status.write(f"📚 Setting up learning path...")
                                    elif 'search' in fname:
                                        status.write(f"🔍 Searching the Web...")
                                    else:
                                        status.write(f"⚙️ Running: `{fname}`...")
                                        
                                if getattr(part, 'text', None):
                                    response_text += part.text
                    
                    status.update(label="Response ready!", state="complete", expanded=False)
                    
                    if response_text:
                        import json
                        import re
                        try:
                            # Catch perfect JSON leaks
                            parsed = json.loads(response_text.strip())
                            if isinstance(parsed, dict) and "thought" in parsed:
                                response_text = "I'm analyzing the best learning paths for that topic..."
                        except Exception:
                            pass
                            
                        # Robust cleanup for Llama 3/Local models leaking partial JSON tool calls and internal thoughts
                        # Matches things like {"name": "...", "arguments": {"}}
                        response_text = re.sub(r'\{[^}]*"name"\s*:\s*"[^"]*".*?\}\}?', '', response_text, flags=re.DOTALL)
                        response_text = re.sub(r'\{[^}]*":\s*"log_conversation".*?\}\}?', '', response_text, flags=re.DOTALL)
                        
                        # Remove internal python-style comments that local models use to talk to themselves
                        # But be careful not to remove comments inside markdown code blocks.
                        # Since local models often put `# thoughts` outside code blocks, we can try to clean it up:
                        lines = response_text.split('\n')
                        cleaned_lines = []
                        in_code_block = False
                        for line in lines:
                            if line.strip().startswith('```'):
                                in_code_block = not in_code_block
                            if not in_code_block and line.strip().startswith('# ') and not line.strip().startswith('# #'):
                                # It's a markdown header or a leaked thought. 
                                # Local models often say "# Get user's history..."
                                # Let's keep it unless it looks like an action description
                                lower_line = line.lower()
                                if any(verb in lower_line for verb in ["get user's", "now the user", "now i will", "for example if they"]):
                                    continue
                            cleaned_lines.append(line)
                        response_text = '\n'.join(cleaned_lines).strip()
                        
                        if "Here is a response based on the conversation so far:" in response_text:
                            response_text = response_text.split("Here is a response based on the conversation so far:")[1].strip()

                        # Fix MathJax formatting for Streamlit
                        response_text = response_text.replace(r'\(', '$').replace(r'\)', '$')
                        response_text = response_text.replace(r'\[', '$$').replace(r'\]', '$$')

                        agent_mapping = {
                            "root_agent": "AI Tutor",
                            "dsa_tutor": "DSA Tutor",
                            "dsa_solver": "DSA Solver",
                            "code_generator": "Code Generator",
                            "code_reviewer": "Code Reviewer",
                            "developer_tutor": "Developer Tutor",
                            "system_design_tutor": "System Design Tutor",
                            "search_agent": "Search Agent",
                            "account_agent": "Account Manager"
                        }
                        final_display_name = agent_mapping.get(last_author, last_author.replace("_", " ").title())
                        
                        st.write(f"**{final_display_name}**")
                        render_message_with_mermaid(response_text)
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_text,
                            "sender_name": last_author
                        })
                        
                        # Native background DB logging
                        try:
                            import json
                            metadata = json.dumps({"sender": last_author})
                            db_manager.log_interaction(
                                st.session_state.user_id,
                                st.session_state.session_id,
                                prompt,
                                response_text,
                                metadata
                            )
                        except Exception as e:
                            st.caption(f"Error logging to DB: {e}")
                        
                        # Rerun to update Sidebar if path was created
                        st.rerun()
                    else:
                        st.info("I've processed your request behind the scenes, but I don't have anything else to add right now. What would you like to learn next?")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "I've processed your request behind the scenes, but I don't have anything else to add right now. What would you like to learn next?",
                            "sender_name": "AI Tutor"
                        })
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    if not st.session_state.authenticated:
        login_page()
    else:
        chat_page()
