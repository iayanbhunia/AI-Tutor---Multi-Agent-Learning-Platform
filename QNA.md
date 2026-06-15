# AI Tutor — Examiner Q&A Reference

> Covers every likely question an examiner could ask — from one-word answers to 2-paragraph deep explanations. Organized by topic area.

---

## Table of Contents

1. [Project Overview & Purpose](#1-project-overview--purpose)
2. [Tech Stack Questions](#2-tech-stack-questions)
3. [System Architecture Questions](#3-system-architecture-questions)
4. [AI & Agent Questions (Google ADK)](#4-ai--agent-questions-google-adk)
5. [Database Questions](#5-database-questions)
6. [Quiz System Questions](#6-quiz-system-questions)
7. [Syllabus & Onboarding Questions](#7-syllabus--onboarding-questions)
8. [WebSocket & Real-time Questions](#8-websocket--real-time-questions)
9. [Frontend & UI Questions](#9-frontend--ui-questions)
10. [LLM & AI Model Questions](#10-llm--ai-model-questions)
11. [Security & Validation Questions](#11-security--validation-questions)
12. [Design Decision Questions](#12-design-decision-questions)
13. [Scalability & Limitations Questions](#13-scalability--limitations-questions)
14. [Code-Level Deep Dives](#14-code-level-deep-dives)
15. [Comparison & Alternative Questions](#15-comparison--alternative-questions)
16. [Future Work & Improvements](#16-future-work--improvements)

---

## 1. Project Overview & Purpose

---

**Q: What is the AI Tutor project in one sentence?**

> An intelligent, personalized learning platform where a multi-agent AI system teaches users topic-by-topic and enforces mandatory quizzes before allowing progress to the next topic.

---

**Q: What problem does this project solve?**

> Traditional online learning platforms let users passively skip through content without verifying comprehension. This project solves that by combining adaptive AI tutoring with a mandatory, server-enforced quiz checkpoint system that prevents users from advancing to a new topic unless they demonstrate understanding of the previous one. The AI also dynamically inserts remedial modules when a user fails a quiz, personalizing the curriculum in real time.

---

**Q: What is the core innovation of this project?**

> The core innovation is the **multi-layer quiz gatekeeping system**. Most AI tutors are purely conversational and can be manipulated into skipping assessments. In this system, quiz enforcement happens at five independent levels — the AI prompt, the WebSocket backend, the database flag, the tool-level API, and the client UI — making it impossible to bypass even with direct API calls.

---

**Q: Who is the target user of this system?**

> Students and self-learners who want a structured, personalized curriculum in subjects like Python programming, Data Structures, Web Development, iOS Development, Data Science, Machine Learning, and System Design. The system adapts to their current skill level through the onboarding process and evolves the syllabus based on quiz performance.

---

**Q: What makes this different from ChatGPT or a generic AI chatbot?**

> A generic chatbot has no memory of what it taught you, no structured curriculum, no enforced assessments, and no adaptive remediation. This project adds: (1) a dynamically generated, personalized syllabus persisted in a database, (2) a hierarchical multi-agent system where different specialist AIs handle different question types, (3) mandatory quiz checkpoints enforced at the backend level, and (4) automatic syllabus mutation that inserts targeted remedial modules when the user fails specific quiz questions.

---

**Q: What is the application's core loop?**

> Onboard → Teach → Quiz → Evolve Syllabus → Teach again. After signup, the system generates a personalized JSON syllabus via a multi-turn conversation. The AI then teaches each topic using specialist agents. After each topic, a mandatory quiz is triggered. Quiz results either advance the user or inject granular remedial modules into the syllabus, which are taught next before proceeding.

---

**Q: How many specialist agents are in the system?**

> Six — `theory_agent`, `coding_agent`, `math_agent`, `assessment_agent`, `visualization_agent`, and `search_agent`.

---

## 2. Tech Stack Questions

---

**Q: What is the tech stack of the AI Tutor project?**

> - **Frontend**: React, Vite, TailwindCSS, Zustand (state management), ReactMarkdown
> - **Backend**: FastAPI, Uvicorn (ASGI server)
> - **Agent Framework**: Google ADK (Agent Development Kit)
> - **Database**: SQLite with SQLAlchemy ORM (WAL mode)
> - **LLM**: Google Gemini API (default) or local Ollama — switchable via one env var
> - **LLM Bridge**: litellm (universal LLM proxy library)

---

**Q: Why FastAPI over Flask or Django?**

> FastAPI was chosen because it is async-first by design, which is essential for WebSocket streaming. Flask is synchronous by default and Django is heavyweight with unnecessary overhead for a pure API server. FastAPI also provides automatic OpenAPI documentation via Pydantic models, which helps during development.

---

**Q: Why React and not plain HTML/JS or another framework?**

> The application requires complex, reactive UI state — streaming text that updates in real-time, quiz overlay logic, a locked/unlocked input, and Zustand-based global state shared across components. React's component model and fine-grained re-rendering make this manageable. Plain HTML/JS would require manual DOM manipulation for every streaming chunk, which is error-prone at this scale.

---

**Q: Why Zustand for state management instead of Redux?**

> Zustand has a much simpler API — a single `create()` call with no reducers, actions, or boilerplate. It also ships a `persist` middleware out of the box for localStorage sync. Redux adds significant complexity without benefit for a project of this size. Zustand's selector-based subscriptions also mean components re-render only when the specific slice of state they use changes.

---

**Q: Why SQLite and not PostgreSQL or MongoDB?**

> SQLite requires zero external infrastructure — no running database server, no connection pool configuration. For a final year project running on a single machine, this is ideal. SQLite in WAL (Write-Ahead Logging) mode can handle concurrent reads and writes efficiently, which is sufficient for the WebSocket chat load. PostgreSQL would be needed for multi-process or multi-machine deployment.

---

**Q: What is Vite and why is it used?**

> Vite is a modern frontend build tool that serves source files natively via ES modules during development (extremely fast HMR — Hot Module Replacement) and bundles them with Rollup for production. It's faster than Webpack/Create React App, especially for TypeScript projects.

---

**Q: What is TailwindCSS?**

> TailwindCSS is a utility-first CSS framework. Instead of writing separate CSS files, you apply small utility classes directly in JSX (e.g., `bg-zinc-900 rounded-xl p-4`). It prevents CSS file bloat, avoids naming conflicts, and makes styles co-located with the component that uses them.

---

**Q: What is Google ADK?**

> Google ADK (Agent Development Kit) is Google's framework for building multi-agent AI systems. It provides abstractions for defining agents with instructions and tools, routing between agents via `transfer_to_agent`, persisting conversation state via `SessionService`, and streaming responses via `runner.run_async()`.

---

**Q: What is litellm?**

> litellm is a Python library that provides a single unified API (`litellm.completion()`) that routes LLM requests to different providers — Google Gemini, OpenAI, Anthropic, local Ollama — by interpreting the model name prefix. This means you can switch from Gemini to a local Llama model by changing one environment variable without touching any application code.

---

**Q: What is the role of `aiosqlite` in the project?**

> `aiosqlite` is an async SQLite driver. ADK's `DatabaseSessionService` uses it to read/write session state asynchronously without blocking the FastAPI event loop. The application's `DBManager` uses standard synchronous SQLAlchemy — both share the same SQLite file, coexisting via WAL mode.

---

## 3. System Architecture Questions

---

**Q: Describe the overall system architecture.**

> The system has three main layers: (1) a React SPA frontend that communicates via REST and WebSocket; (2) a FastAPI backend that handles all HTTP/WebSocket traffic, serves the compiled frontend as static files, and manages the database; and (3) a Google ADK agent layer where a root orchestrator agent routes messages to specialist subagents. Two external services are used — the LLM API (Gemini or Ollama) and the mermaid.ink API for diagram rendering.

---

**Q: How does the frontend communicate with the backend?**

> Two channels: (1) **REST HTTP** — for auth, path management, onboarding, and quiz operations. (2) **WebSocket** — for the real-time chat. A persistent WebSocket connection is opened when the user selects a learning path, and all chat messages stream bidirectionally through it for the duration of the session.

---

**Q: What is the directory structure of the project?**

> Three main directories: `ai_tutor_agent/` (Python agent code — root agent, 9 subagents, shared tools, utils), `fastapi_app/` (FastAPI backend — main.py, quiz_engine.py, syllabus_engine.py), and `frontend/src/` (React app — components, store, App.tsx). The legacy `streamlit_app.py` has been removed; the project exclusively uses the React + FastAPI stack.

---

**Q: How is the compiled frontend served?**

> FastAPI mounts the compiled React build (`frontend/dist/`) as static files at `/app`. A root redirect sends `/` to `/app/index.html`. This means a single Uvicorn process serves both the API and the SPA with no separate web server (no Nginx needed in development).

---

**Q: What happens when the server restarts mid-session?**

> Because ADK uses `DatabaseSessionService`, all agent conversation history is persisted to SQLite and survives restarts. The quiz pending flag is also stored in the `learning_paths` table, so on reconnect the frontend calls `GET /api/quiz/pending` and if a quiz was in progress, it automatically restores the quiz overlay and re-locks the chat input.

---

**Q: How does the system handle multiple users?**

> Each user has a unique `user_id` and each chat session has a unique `session_id`. All DB queries are filtered by these IDs. FastAPI handles multiple concurrent WebSocket connections asynchronously. Each WebSocket handler creates its own ADK `Runner` instance keyed to the correct `(user_id, session_id)` pair.

---

**Q: What is the `adk.yaml` file?**

> The ADK configuration file that tells the ADK runner which agent to load as the root agent. It maps the app name (`ai_tutor`) to the Python module containing `root_agent`.

---

## 4. AI & Agent Questions (Google ADK)

---

**Q: What is the agent pattern used?**

> **Hierarchical Orchestrator** pattern. One root agent acts as a dispatcher and routes all messages to specialist leaf agents. No leaf agent can route to another — they are terminal. Control always returns to the root after a specialist completes.

---

**Q: What is a terminal agent?**

> A terminal agent is a specialist agent with no `sub_agents` list and no tools. It can only respond with text. This is enforced via the instruction prompt: *"You are a terminal agent. You MUST NOT use any tools. You MUST NOT use transfer_to_agent. TEXT ONLY."* Terminal agents in this project are: `theory_agent`, `coding_agent`, `math_agent`, and `visualization_agent`.

---

**Q: How does the root agent route messages to the correct specialist?**

> The root agent's instruction prompt contains a routing table mapping question types to agent names. When it decides to route, it calls the `transfer_to_agent` built-in ADK tool with the target agent name. FastAPI intercepts this function call in the event stream and sends a `{type: "status"}` event to the UI showing which specialist is being consulted.

---

**Q: What tools does the root agent have?**

> Five tools: `get_user_history` (fetch recent chat from DB), `create_learning_path_tool` (create a path record), `get_learning_paths_tool` (list all paths), `get_current_learning_path_context` (get active syllabus), and `update_learning_path_details` (save syllabus — contains the quiz enforcement gateway).

---

**Q: What is the role of the assessment agent?**

> The assessment agent has exactly one job: call `trigger_topic_quiz(topic_name)`. It has no other tools and cannot teach. It also has an escape hatch — if the incoming message is a `[System Action]` confirmation that a quiz was completed, it returns `"Quiz sequence finished. Returning to tutor."` instead of triggering a new quiz, preventing an infinite loop.

---

**Q: How does the system prevent the AI from looping infinitely?**

> Three mechanisms: (1) The root agent's instruction says "ONE action per turn — no chaining." (2) The assessment agent's escape hatch prevents re-triggering on `[System Action]` messages. (3) The root agent is explicitly told: "After a specialist returns a response, output it as text and stop. Do NOT transfer again."

---

**Q: What is `runner.run_async()` and how is it used?**

> `runner.run_async(user_id, session_id, new_message)` is the ADK entry point that starts an agent execution turn. It's an async generator that yields `Event` objects — each event can be a function call, a function result, or a text chunk from the LLM. FastAPI iterates over these events in a loop, forwarding relevant ones to the WebSocket.

---

**Q: How does ADK maintain conversation history?**

> ADK's `DatabaseSessionService` stores all turns (user messages, agent responses, function calls, function results) in its own tables in the SQLite database. This session context is automatically included in every subsequent `run_async` call for the same `session_id`, so the root agent has full memory of the conversation without needing to call `get_user_history`.

---

**Q: What is the difference between `sub_agents` and `tools` in ADK?**

> `tools` are Python functions the agent can call (like DB queries). `sub_agents` are other Agent objects the root agent can hand off control to via `transfer_to_agent`. Tools return data; sub_agents produce responses and stream text. Tools are synchronous tool calls within a turn; sub_agents represent full agent execution turns.

---

**Q: How does the visualization agent render diagrams?**

> The `visualization_agent` generates Mermaid.js diagram code as a markdown code block. The frontend's `ChatInterface` intercepts `language-mermaid` code blocks in the ReactMarkdown renderer and converts them to image URLs via the `mermaid.ink` API (`https://mermaid.ink/img/{base64_encoded_state}`). The image is rendered as an `<img>` tag with a click-to-zoom lightbox.

---

**Q: Why is the search agent different from the other terminal agents?**

> The `search_agent` is the only non-assessment specialist that has a tool — `google_search` (when using Gemini) or a `web_search` mock (when using Ollama). It cannot use `transfer_to_agent`, but it can call the search tool to fetch real-time web results. It degrades gracefully in offline mode by returning a mock response instead of failing.

---

**Q: What happens if the LLM breaks the one-action-per-turn rule?**

> The root agent's instruction explicitly says "ONE action per turn" and "NEVER do two of these in the same turn." If the LLM still violates this (hallucination), the ADK runner processes the first action and the second may be ignored or cause an error. The retry config (15 attempts for Gemini) also handles transient model errors without crashing.

---

**Q: How does context injection work for the agent?**

> When the first message of a WebSocket session is received, FastAPI prepends the active syllabus to the prompt: `"[System: Active Syllabus context:\n{syllabus_json}]\n\nUser's actual message"`. This ensures the root agent has full curriculum context on turn 1 without needing a tool call. From turn 2 onward, this context lives in ADK's session history.

---

## 5. Database Questions

---

**Q: What database does the project use?**

> SQLite, accessed via SQLAlchemy ORM with WAL (Write-Ahead Logging) mode enabled.

---

**Q: What are the four main tables in the database?**

> 1. `users` — user identity (user_id PK, name, created_at)
> 2. `interactions` — chat history (session_id, user_id, agent_name, query, response, metadata_json, timestamp)
> 3. `student_profiles` — per-subject skill tracking (user_id, subject, level, details JSON)
> 4. `learning_paths` — courses (user_id, session_id unique, subject, title, syllabus JSON, quiz_pending_module)

---

**Q: What is WAL mode and why is it used?**

> WAL (Write-Ahead Logging) is a SQLite journal mode where writes go to a separate `-wal` file instead of directly modifying the main database. Readers access the main file unblocked while writes happen concurrently. Without WAL, a write transaction locks the entire database, which would cause the WebSocket chat handler to block when logging interactions while simultaneously reading the quiz pending flag. WAL is enabled via `PRAGMA journal_mode=WAL` on every new connection.

---

**Q: What are the four SQLite PRAGMAs applied and why?**

> - `PRAGMA journal_mode=WAL` — concurrent reads during writes
> - `PRAGMA synchronous=NORMAL` — reduce fsync calls (safe under WAL)
> - `PRAGMA cache_size=-64000` — allocate 64 MB of RAM for page cache
> - `PRAGMA temp_store=MEMORY` — use RAM for temp tables instead of disk files
> These together significantly improve SQLite performance for a concurrent WebSocket application.

---

**Q: What is the Singleton pattern and why is it used for DBManager?**

> A Singleton ensures exactly one instance of `DBManager` exists per process. Python's `__new__` method is overridden to check if `_instance` is already set and return it if so, only creating a new engine on the first instantiation. This prevents multiple SQLAlchemy engines from being created, which would waste connections and cause confusion in SQLite's locking model.

---

**Q: How is database schema migration handled?**

> There is no formal migration tool (like Alembic). Instead, `DBManager.__new__` runs `ALTER TABLE ... ADD COLUMN` statements in `try/except` blocks at every startup. SQLite will raise an error if the column already exists — the `except` catches and ignores it. This pattern is simple and reliable for SQLite, though it doesn't support column removal or type changes.

---

**Q: What is stored in `learning_paths.syllabus`?**

> A JSON string representing the full course structure. Initially from the onboarding engine: `{modules: [{title, topics[]}]}`. Over time, the quiz answer endpoint mutates this JSON to add `completed_topics[]` arrays to modules and inject `Remedial: {topic}` module objects.

---

**Q: What is `quiz_pending_module` and what does it control?**

> It is a TEXT column in `learning_paths` that stores the name of the topic currently being quizzed, or `NULL` if no quiz is active. When non-NULL, the WebSocket handler drops all non-hidden incoming messages and returns a `quiz_required` error. This is the database-level enforcement of the quiz system. It is set by `set_quiz_pending()` and cleared by `clear_quiz_pending()`.

---

**Q: Why does the project use two separate DB access methods for the same SQLite file?**

> `DBManager` uses synchronous SQLAlchemy for application tables (users, interactions, profiles, paths). ADK's `DatabaseSessionService` uses async `aiosqlite` for its own session/conversation state tables. They share the same `.db` file but have completely separate table namespaces. WAL mode allows them to coexist without locking conflicts.

---

**Q: What is the `metadata_json` column in `interactions` used for?**

> Currently stored as `'{}'` (an empty JSON object) on every interaction. It is reserved for future use — potential uses include storing the agent routing trace, response confidence scores, or per-message metadata tags. The column was added via auto-migration.

---

## 6. Quiz System Questions

---

**Q: How many questions does each quiz have?**

> Five questions. The quiz engine prompt instructs: generate the next question if fewer than 5 have been asked, and produce a `final_review` instead if 5 or more have been completed.

---

**Q: What question types does the quiz support?**

> Two types: `mcq` (multiple choice, with 4 options) and `short_answer` (free text textarea). The question type is determined by the LLM based on what best tests the topic. The `QuizOverlay` renders option buttons for MCQ and a `<textarea>` for short answer.

---

**Q: How does the quiz adapt difficulty?**

> The `evaluate_and_generate_next()` prompt tells the LLM: "If the answer was correct, make the next question slightly harder. If wrong, make it the same difficulty or easier." The quiz history (all prior Q&As) is passed with every request, so the LLM has full context of the session's performance.

---

**Q: What happens when a user fails a quiz?**

> The `final_review` object in the quiz completion response now contains a `wrong_topics[]` array listing the **exact subtopic tested by each wrong answer** (one entry per incorrect question). For each topic in this list, the backend injects a dedicated `Remedial: {topic}` module into the syllabus immediately after the current module — so each failed subtopic gets its own focused revision module. If `needs_remedial` is true but `wrong_topics` is empty, a single generic remedial module is injected as a fallback.

---

**Q: What happens when a user passes a quiz?**

> The topic is stamped into the parent module's `completed_topics[]` array in the syllabus JSON. The `quiz_pending_module` flag is cleared, the chat unlocks, and a hidden `[System Action]` message triggers the root agent to start teaching the next topic.

---

**Q: How does the quiz prevent the user from skipping it by refreshing the page?**

> The `quiz_pending_module` flag is stored in the database, not in memory or localStorage. On every WebSocket reconnection, `ChatInterface` calls `GET /api/quiz/pending`. If the flag is non-null, the frontend automatically re-fetches the first quiz question and reopens the `QuizOverlay`, re-locking the chat.

---

**Q: What are the five layers of quiz enforcement?**

> 1. **LLM Prompt** — root agent is instructed to always transfer to assessment after teaching.
> 2. **WebSocket Server-Side Block** — backend checks `quiz_pending_module` *before* every non-hidden message; if non-null, it sends a `quiz_required` event with the module name and drops the message — it never reaches the LLM. The `set_quiz_pending()` DB call now happens directly in the WS handler when a `trigger_topic_quiz` function call is intercepted.
> 3. **Tool-Level Rejection** — `update_learning_path_details` checks `completed_topics[]` and rejects DB writes if the old topic wasn't quizzed.
> 4. **UI Input Lock** — the `<input>` is `disabled` and an amber animated lock banner with 🔒 appears above the input when `quizRequired` is true. The input border turns amber and placeholder changes to "🔒 Complete the quiz to continue...".
> 5. **Page Refresh Recovery** — `GET /api/quiz/pending` on reconnect restores and re-locks the quiz state.

---

**Q: How is the quiz history maintained?**

> The quiz history is maintained entirely on the client side (inside `QuizOverlay` local state) as an array of `{question, user_answer}` objects. This full array is sent to the backend with every answer submission at `POST /api/quiz/answer`. The backend passes it to the LLM so it can evaluate the latest answer in context.

---

**Q: Why is the quiz history kept client-side rather than in the database?**

> Quiz history is transient — it's only needed for the 5-question session. Storing it in the DB would require additional tables and cleanup logic. Passing it in the request body is simpler, and since the quiz must be completed in one sitting, there is no need for cross-session persistence of individual question answers.

---

**Q: What is a remedial module?**

> A dynamically injected syllabus module created when a user fails specific quiz questions. With the new per-question granularity, **one remedial module is created per failed subtopic** — so failing two questions creates two separate remedial modules. The structure is:
> ```json
> {
>   "title": "Remedial: Binary Search edge cases",
>   "status": "pending",
>   "topics": ["Review: Binary Search edge cases", "Practice exercises"]
> }
> ```
> It is inserted directly after the module that triggered the quiz, so the next thing the AI teaches is exactly the weak area identified.

---

**Q: What is the `trigger_topic_quiz` function and who calls it?**

> It is a Python function in `shared_tools/path_tools.py`, wrapped as an ADK `FunctionTool`. Only the `assessment_agent` has access to it. When called, it returns `{status: "quiz_triggered", _internal_action: "open_quiz"}`. FastAPI's WebSocket handler intercepts the *function call event* in the ADK event stream, calls `db_manager.set_quiz_pending(session_id, topic_name)` directly, sends a `"Preparing Mandatory Quiz"` status message, and then fires the `trigger_quiz` WebSocket event. The return value of the tool itself is informational only.

---

**Q: How does the quiz overlay know what question to start with?**

> ChatInterface pre-fetches the first question immediately after receiving `trigger_quiz`. It calls `POST /api/quiz/start` and stores the response in Zustand as `quizPreloadedData`. When `QuizOverlay` mounts, it reads this preloaded data instantly — there is zero wait time for the user.

---

## 7. Syllabus & Onboarding Questions

---

**Q: How is the personalized syllabus generated?**

> During onboarding, a multi-turn conversation in `OnboardingModal` sends user answers to `POST /api/paths/onboarding/chat`. The `syllabus_engine.handle_onboarding_chat()` function reconstructs the full conversation as a message list and calls the LLM with a system prompt instructing it to act as a curriculum designer. It asks 1-2 follow-up questions before generating a structured JSON syllabus tailored to the user's subject and skill level.

---

**Q: What format does the syllabus use?**

> ```json
> {
>   "modules": [
>     {
>       "title": "Module Name",
>       "topics": ["Topic 1", "Topic 2", "Topic 3"]
>     }
>   ]
> }
> ```
> Over time, `completed_topics[]` arrays and `status` fields are added by the quiz system. Remedial modules are inserted with `"title": "Remedial: {topic}"`.

---

**Q: How many questions does the onboarding ask?**

> The system prompt tells the LLM to ask "1 or 2 follow-up questions" before generating the syllabus. In practice it typically asks one (skill level) before producing the full curriculum.

---

**Q: What happens if the LLM fails to return valid JSON during onboarding?**

> `_extract_json()` first tries direct `json.loads()`, then regex-extracts from inside markdown fences. If both fail, it returns `{}`. The calling code then falls back to returning `{status: "ongoing", question: "Could you elaborate on that?"}`, keeping the onboarding conversation alive without crashing.

---

**Q: How are option chips shown during onboarding?**

> When the LLM returns `{status: "ongoing", options: ["Beginner", "Intermediate", "Advanced"]}`, the frontend renders these as clickable indigo buttons. Clicking one calls `handleSend(undefined, optionText)`, submitting the selection without requiring the user to type.

---

**Q: How is the syllabus saved after onboarding?**

> After the LLM returns `status: "complete"`, the `OnboardingModal` calls `POST /api/paths/create` with: `{user_id, session_id: path_${Date.now()}, subject, title, syllabus: JSON.stringify(syllabus)}`. FastAPI calls `db_manager.create_learning_path()` then `db_manager.update_learning_path_details()` to store the JSON in the `learning_paths.syllabus` column.

---

**Q: How does the AI agent know the current syllabus during chat?**

> Two ways: (1) On the first message of a session, FastAPI prepends the full syllabus JSON to the prompt. (2) On any subsequent message, the root agent can call the `get_current_learning_path_context` tool to fetch the current syllabus from the DB.

---

**Q: What does `syllabus_engine.py` have in common with `quiz_engine.py`?**

> Both are stateless modules using `litellm.completion()` directly (not ADK). Both use the same `_get_litellm_model()` and `_extract_json()` helper pattern. Both rely on JSON-mode prompting and return parsed dict results. Neither maintains any state — all state lives in the DB.

---

## 8. WebSocket & Real-time Questions

---

**Q: Why use WebSocket instead of HTTP polling or Server-Sent Events?**

> WebSocket is bidirectional — the client sends messages and the server streams chunks back on the same connection. Server-Sent Events (SSE) are unidirectional (server → client only), so you'd need a separate HTTP request per user message. HTTP long-polling adds latency. WebSocket is the natural choice for interactive chat with streaming responses.

---

**Q: What is the WebSocket endpoint URL?**

> `ws://localhost/ws/chat/{session_id}?user_id={user_id}`

---

**Q: What WebSocket message types are sent from server to client?**

> | Type | Meaning |
> |---|---|
> | `chunk` | A streaming text token from the active agent |
> | `status` | Agent routing update (e.g., "Consulting Coding Agent...") |
> | `trigger_quiz` | Quiz checkpoint fired; lock UI and open overlay |
> | `quiz_required` | Server rejected the message — quiz is pending |
> | `done` | Agent turn complete |

---

**Q: What message types are sent from client to server?**

> JSON objects with `{prompt: string, hidden?: boolean}`. The `hidden` flag tells the server to skip logging and skip the quiz pending check — used for system action messages after quiz completion. Hidden messages also carry `wrongTopics[]` and `score` in the `[System Action]` prompt text so the root agent knows which remedial topics were added.

---

**Q: How is streaming text rendered in the UI?**

> Each `chunk` event calls `updateLastMessage(content)` in Zustand, which appends the chunk to the last message's `response` string. Because Zustand uses immutable updates, React only re-renders the last message bubble. The previous messages are not affected.

---

**Q: What is the `hidden` flag in WebSocket messages?**

> A boolean sent by the client to indicate that this is a system-generated message (not a real user message). When `hidden: true`, the backend skips: (1) logging the interaction to DB, (2) the quiz pending check. This is used for the `[System Action]` message sent after quiz completion so it can always reach the agent regardless of DB state.

---

**Q: How does the WebSocket connection handle disconnection?**

> The WebSocket handler loop is wrapped in `try/except WebSocketDisconnect: pass`. When the client disconnects (browser close, refresh, navigation), the exception is raised, the loop exits cleanly, and the connection is closed gracefully. The ADK session and DB state are fully preserved.

---

**Q: What happens during the first WebSocket message of a session?**

> FastAPI detects `not context_injected` (a flag initialized to `False` per connection). It prepends the active syllabus JSON to the user's prompt: `"[System: Active Syllabus context:\n{json}]\n\n{user_prompt}"`. The `context_injected` flag is then set to `True`, so subsequent messages are sent as-is.

---

**Q: How does the routing status pill work in the UI?**

> When FastAPI intercepts a `transfer_to_agent` function call in the ADK event stream, it sends `{type: "status", content: "Consulting Theory Agent..."}` over the WebSocket. `ChatInterface` sets `streamingStatus` state, which renders a small animated pill below the last message. When the first `chunk` arrives, `streamingStatus` is cleared and the actual text starts appearing.

---

## 9. Frontend & UI Questions

---

**Q: What is the component hierarchy of the frontend?**

> `App.tsx` → (if logged in) `Sidebar` + `ChatInterface` + `QuizOverlay` + `UserProfile` in main layout. If `showOnboarding` is true, `OnboardingModal` is also rendered. If no user, `AuthView` is rendered instead.

---

**Q: How does App.tsx act as an auth guard?**

> `App.tsx` reads `user` from Zustand. If `user === null`, it renders only `<AuthView />`. Once `setUser()` is called with a valid user, Zustand updates, React re-renders, and the full application layout appears. No routing library is used — it is a single-page conditional render.

---

**Q: What state is persisted to localStorage?**

> Only `{user, activePath, modelMode}` via Zustand's `persist` middleware. Chat history, quiz state, quiz flags (`quizActive`, `quizRequired`, `quizModule`, etc.) are session-only (in-memory) and are reset on page refresh.

---

**Q: What is `quizRequired` in the Zustand store?**

> `quizRequired` is a boolean field in the Zustand store that controls whether the chat input is hard-locked. It is set to `true` when the server sends a `trigger_quiz` or `quiz_required` WebSocket event, and explicitly cleared to `false` by `QuizOverlay.handleClose()` and the `quiz_completed` window event listener in `ChatInterface`. Unlike `quizActive` (which controls the overlay), `quizRequired` controls the input lock and the amber banner. It is not persisted to localStorage (resets on refresh, but `GET /api/quiz/pending` restores it).

---

**Q: How does `ChatInterface` know when to reconnect WebSocket?**

> A `useEffect` with `[activePath, user]` dependencies. When either changes (e.g., user selects a different path), the old WebSocket is closed in the cleanup function and a new one is opened to the new `session_id`.

---

**Q: How are Mermaid diagrams rendered without the mermaid.js library?**

> ReactMarkdown's `code` renderer is overridden to detect `language-mermaid` blocks. Instead of client-side rendering (which would require the 2 MB mermaid.js bundle), the diagram spec is base64-encoded and passed as a URL parameter to `https://mermaid.ink/img/{b64}`. The API returns an SVG image, which is rendered as an `<img>` tag.

---

**Q: What happens if mermaid.ink fails to render a diagram?**

> The `<img>` tag's `onError` event sets `hasError = true` in `MermaidRenderer` local state. This triggers the fallback: an amber warning banner and the raw Mermaid code shown in a `<pre>` block so the user can at least read it.

---

**Q: How do `QuizOverlay` and `ChatInterface` communicate?**

> Via a custom DOM event: `window.dispatchEvent(new CustomEvent('quiz_completed', {detail: {module, wrongTopics, score}}))`. `QuizOverlay` fires it when the quiz finishes, passing `wrong_topics[]` and the score from the `final_review`. `ChatInterface` listens via `window.addEventListener('quiz_completed', handler)` and uses these details to (1) clear `quizRequired`, and (2) send the hidden `[System Action]` WebSocket message that informs the agent which remedial topics were added. This pattern avoids lifting state all the way up through `App.tsx` and is cleaner than a Zustand event bus for one-way signals.

---

**Q: What is the `quizPreloadedData` pattern?**

> When the server sends `trigger_quiz`, `ChatInterface` immediately fetches `POST /api/quiz/start` and stores the first question in `quizPreloadedData` (Zustand). When `QuizOverlay` mounts, it reads this preloaded data instead of making another network request — the quiz opens instantly with no loading delay.

---

**Q: What is the `ErrorBoundary` component used for in ChatInterface?**

> It wraps the image renderer in markdown. If rendering an `<img>` tag throws a React error (e.g., a malformed src), the `ErrorBoundary` catches it via `getDerivedStateFromError` and renders a fallback "Failed to load image" message instead of crashing the entire chat view.

---

**Q: How does the Sidebar's syllabus view handle different JSON formats?**

> The syllabus can be stored in multiple legacy formats depending on which code path created it. `Sidebar.tsx` normalizes all three:
> 1. `Array` → use directly
> 2. `{syllabus: [...]}` → extract `syllabus` key
> 3. `{modules: [...]}` → map `title/topics` to `{module, subtopics, status}` format

---

**Q: What triggers the Sidebar to re-render the syllabus after a quiz?**

> `QuizOverlay` dispatches `window.dispatchEvent(new CustomEvent('path_updated'))` after quiz completion. `Sidebar` listens for this event via `window.addEventListener('path_updated', handlePathUpdated)` and calls `fetchPathDetails(activePath)` to re-fetch the mutated syllabus from the DB.

---

## 10. LLM & AI Model Questions

---

**Q: What is the default LLM model?**

> `gemini-2.5-flash`

---

**Q: How do you switch to a local Ollama model?**

> Change `AGENT_MODEL=ollama/llama3.1` in `ai_tutor_agent/.env`. No code changes are required. The `get_model()` function in `llm_config.py` detects the `/` in the model name and wraps it in ADK's `LiteLlm` adapter. The quiz and syllabus engines use the same env var with `_get_litellm_model()`.

---

**Q: What is the retry configuration for Gemini?**

> `HttpRetryOptions(initial_delay=2, attempts=15)`. FastAPI calls the LLM up to 15 times with exponential backoff, starting at 2 seconds. This handles Gemini API rate limits and transient failures transparently.

---

**Q: Why does `litellm.completion()` need `"gemini/gemini-2.5-flash"` but ADK only needs `"gemini-2.5-flash"`?**

> litellm requires a provider prefix to know which API endpoint to call. ADK's native Gemini connector handles routing internally and doesn't need the prefix. The `_get_litellm_model()` function in the engines adds `"gemini/"` when the model string contains no `/`.

---

**Q: What is the temperature setting for onboarding?**

> `temperature=0.7` in `syllabus_engine.py`. This gives the LLM enough creativity to generate varied, personalized curricula while keeping responses structured. The quiz engine uses the default temperature (typically 1.0) for diverse question generation.

---

**Q: Can the system work completely offline?**

> Yes, with Ollama. Set `AGENT_MODEL=ollama/llama3.1` (or any locally available Ollama model). The syllabus and quiz engines route through litellm to `http://localhost:11434`. The only feature that degrades is web search (the search agent returns a mock response instead of real results). Mermaid diagrams also require internet for `mermaid.ink`.

---

**Q: How does the system handle LLM responses that wrap JSON in markdown fences?**

> Both `syllabus_engine.py` and `quiz_engine.py` have `_extract_json()` which first tries `json.loads()`. If that fails (because the LLM wrapped it in ` ```json ``` `), it uses `re.search(r'\{.*\}', text, re.DOTALL)` to extract the JSON object from inside the fences.

---

**Q: What is the `response_parser.py` used for?**

> It is a legacy utility from when some agents returned structured JSON objects instead of plain text. It parses known patterns like `{dsa_agent_response: {explanation: "..."}}` and extracts the human-readable text. Current agents are instructed to return plain markdown text, so this parser is rarely invoked today.

---

## 11. Security & Validation Questions

---

**Q: How is authentication handled?**

> Simple string-based identity — `user_id` is sent as a query parameter or in the request body. There are no JWT tokens, no sessions, and no password hashing. The `user_id` is persisted in Zustand localStorage. This is a simplified auth model appropriate for a prototype/final year project.

---

**Q: What are the limitations of the current authentication system?**

> There is no password, no token expiry, no email verification, and no real identity verification. Any user who knows another's `user_id` can access their data. In production, this would need to be replaced with JWT-based auth or OAuth2.

---

**Q: How does the system prevent one user from accessing another user's data?**

> All DB queries are filtered by `user_id`. The WebSocket endpoint takes `user_id` as a query parameter and only fetches that user's sessions and paths. However, since there is no token-based auth, if a user guesses another's `user_id`, they could access their data.

---

**Q: Is user input sanitized before being sent to the LLM?**

> No explicit sanitization — user prompts are passed directly to the LLM. LLM prompt injection is mitigated by the strong system prompts and strict routing rules, but is not fully prevented. For a production system, input sanitization and output validation would be important.

---

**Q: How does the backend validate quiz answers before processing them?**

> Validation is minimal — the endpoint checks that `path` and `syllabus` exist in the DB, then passes the answer directly to the LLM for evaluation. The LLM determines correctness. There is no rule-based answer validation for MCQ (the LLM could theoretically mark a wrong answer as correct).

---

**Q: What is CORS and how is it configured?**

> CORS (Cross-Origin Resource Sharing) controls which origins can make requests to the API. FastAPI's `CORSMiddleware` is configured with `allow_origins=["*"]` — all origins are permitted. This is fine for development but should be locked down to specific frontend domains in production.

---

## 12. Design Decision Questions

---

**Q: Why is the quiz system enforced at the database level rather than just the frontend?**

> Frontend enforcement can be trivially bypassed by a developer using browser DevTools or a custom WebSocket client. By storing `quiz_pending_module` in the database and checking it on every WebSocket message server-side, the system is resilient to any client-side manipulation. The backend now also calls `db_manager.clear_quiz_pending()` inside a `finally`-equivalent block — even if syllabus mutation fails, the quiz lock is still cleared to prevent a permanent dead-lock.

---

**Q: Why store the syllabus as a JSON blob instead of normalized tables?**

> The syllabus structure is dynamic and needs to support runtime mutation — inserting remedial modules at arbitrary positions, adding `completed_topics[]` arrays, and potentially changing module structure. Relational tables would require schema changes or complex JSON-in-SQL queries for every syllabus evolution. A JSON blob gives flexibility at the cost of SQL-level queryability, which is an acceptable trade-off for this application.

---

**Q: Why inject context only on the first message instead of every message?**

> Token efficiency. Repeating the full syllabus JSON in every message would double the token cost of every request. After the first message, the ADK session service stores the full conversation history (including the injected context) in the database. The agent can always call `get_current_learning_path_context` if it needs to re-read the syllabus later in the session.

---

**Q: Why use `window.dispatchEvent` instead of Zustand for the quiz-to-chat bridge?**

> `QuizOverlay` needs to (1) close itself, (2) unlock the chat input, and (3) send a WebSocket message — three actions that span two separate components. A DOM custom event lets `QuizOverlay` broadcast completion to anyone listening without coupling to a specific Zustand action. It's a simple observer pattern for a one-time, directional signal.

---

**Q: Why are teaching agents terminal (no tools) while the assessment agent has one tool?**

> Teaching agents need only to respond with educational text. Giving them tools would create risk of them calling `trigger_topic_quiz` themselves (causing double quiz triggers) or calling `update_learning_path_details` incorrectly. The assessment agent's single tool is tightly scoped to its one job. Terminal agents are a form of capability limiting — they cannot do anything harmful.

---

**Q: Why use `mermaid.ink` over local mermaid.js rendering?**

> The mermaid.js client library is approximately 2 MB. Including it would significantly increase bundle size and require lifecycle management (initialization, re-renders). `mermaid.ink` provides server-side SVG rendering via a URL — the client just loads an `<img>` tag. The trade-off is a dependency on the external service and internet requirement.

---

**Q: Why is the quiz history sent with every answer request instead of fetched from the server?**

> Storing quiz history server-side would require a dedicated table with a 5-row lifecycle (insert on first Q, delete after final answer). Sending it from the client on every request is stateless and simpler — the server doesn't need to track intermediate quiz state. The 5-question session is short enough that re-sending the full history (a few hundred bytes) has negligible overhead.

---

**Q: Why have two separate LLM client layers (ADK + litellm)?**

> ADK manages the agent orchestration and conversation state — it wraps LLM calls with session context, function call handling, and multi-turn reasoning. litellm is used directly for the engines (syllabus and quiz) because those are one-shot structured JSON calls that don't need agent orchestration — just raw LLM completions. Keeping them separate also makes the engines independently testable without the ADK runtime.

---

## 13. Scalability & Limitations Questions

---

**Q: What are the main scalability limitations of the current system?**

> 1. **SQLite is single-writer** — only scales to one server process. Multiple Uvicorn workers would conflict on SQLite writes.
> 2. **No load balancing** — WebSocket connections are sticky to one server instance.
> 3. **No caching** — every syllabus fetch is a DB read; no Redis or in-memory cache.
> 4. **LLM rate limits** — heavily dependent on Gemini API quotas; 15 retries help but are not infinite.
> 5. **In-memory quiz state** — quiz history is kept in `QuizOverlay` local state, lost if the browser crashes mid-quiz.

---

**Q: How would you scale this to handle 1000 concurrent users?**

> Replace SQLite with PostgreSQL or CockroachDB. Replace in-process state with Redis for quiz session data. Use multiple FastAPI workers behind an Nginx load balancer with sticky sessions (or switch to a message queue for WebSocket). Use ADK's database session service with a Postgres backend. Rate limit LLM requests and implement a queue for quiz generation.

---

**Q: What happens if the LLM goes down mid-conversation?**

> The `runner.run_async()` will raise an exception, caught by the WebSocket handler's `except Exception as e`, which sends `{type: "chunk", content: "Error: {e}"}` to the UI. The chat turn ends with an error message, but the session state is preserved. The user can re-send their message.

---

**Q: Is the application production-ready?**

> No. Key missing production requirements: proper authentication (JWT/OAuth2), password hashing, HTTPS enforcement, input sanitization, rate limiting, PostgreSQL for multi-process, Docker containerization, environment-specific configs, logging framework (instead of `print()`), and error monitoring (e.g., Sentry).

---

**Q: What happens if the user closes the browser during a quiz?**

> The `quiz_pending_module` flag remains set in the database. On next login and path selection, `GET /api/quiz/pending` detects the flag, re-fetches the first question from `quiz_engine` (now scoped to the specific topic via `topic_name`), and automatically reopens the `QuizOverlay`. The user's quiz answers are lost (they restart from Q1), but the chat lock is preserved. The `QuizOverlay` close button is not rendered until `status === 'complete'`, so users cannot dismiss the quiz accidentally.

---

**Q: Can the system handle concurrent quiz submissions from the same session?**

> Technically a race condition exists if two requests hit `/api/quiz/answer` simultaneously, but in practice this is impossible since the `QuizOverlay` disables the submit button during `status === 'evaluating'`. The DB write in `update_learning_path_details` is atomic (SQLAlchemy session commit).

---

## 14. Code-Level Deep Dives

---

**Q: Walk me through what happens when a user types a message and presses Enter.**

> 1. `handleSubmit()` in `ChatInterface` validates input, WebSocket state, and `quizRequired` flag — if any fail, the message is not sent.
> 2. Adds user message + empty AI placeholder to `chatHistory` (Zustand).
> 3. `wsRef.current.send({prompt: input})`.
> 4. FastAPI receives, checks `hidden` flag first, then calls `get_quiz_pending()` — if non-null, sends `quiz_required` event and drops message.
> 5. Logs interaction. Injects syllabus on first message.
> 6. `runner.run_async()` starts → root agent processes → routes to specialist.
> 7. FastAPI intercepts `transfer_to_agent` → sends `status` event to UI.
> 8. Specialist generates chunks → FastAPI streams `chunk` events → `updateLastMessage()` appends.
> 9. Root agent triggers quiz → FastAPI intercepts `trigger_topic_quiz` → calls `set_quiz_pending()` directly in WS handler → sends `trigger_quiz`.
> 10. FastAPI sends `done` → logs full response (skipped if `hidden=true`).

---

**Q: How does `update_learning_path_details` enforce quiz completion?**

> The function parses the incoming `syllabus` JSON argument to extract `new_topic = syllabus_dict["current_topic"]`. It then fetches the current DB syllabus and extracts `old_topic`. If `old_topic != new_topic` (the AI is trying to advance), it iterates all modules' `completed_topics[]` arrays. If `old_topic` is not found in any, it returns an error string: `"ERROR: Mandatory Quiz Checkpoint! You MUST trigger the quiz for '{old_topic}'..."`. This error goes back to the root agent as a tool result, forcing it to call `trigger_topic_quiz` before trying again.

---

**Q: How does the ADK event loop work in `main.py`?**

> `runner.run_async()` is an async generator. Each `await event` yields an ADK `Event` object that has `event.get_function_calls()` (list of tool calls) and `event.content.parts` (list of text/data parts). The `for call in func_calls` loop inspects every function call name. Text parts with `part.text` are streamed as `chunk` events. The loop runs until the ADK session turn is complete.

---

**Q: Why does `get_learning_paths_tool` redact the `syllabus` field for other sessions?**

> If the root agent received syllabus JSON for all of a user's sessions simultaneously, it could confuse topics and modules across different subjects (e.g., mixing a Python syllabus with a DSA syllabus). By deleting the `syllabus` key for any path that isn't the current session, only the relevant curriculum is visible. The current session's syllabus is already injected into the context or available via `get_current_learning_path_context`.

---

**Q: How does the `search_agent` switch between real search and mock search?**

> At module load time (not at request time), it evaluates:
> ```python
> if "gemini" in str(get_model()).lower():
>     from google.adk.tools import google_search
>     tools_list.append(google_search)
> else:
>     def web_search(query: str) -> str:
>         return f"Mock search result for '{query}'..."
>     tools_list.append(FunctionTool(web_search))
> ```
> The `tools_list` is resolved at import time, so the agent's capabilities are determined by the environment variable when the server starts, not per-request.

---

**Q: Explain the `_extract_json` function.**

> It is a two-pass JSON extractor used in both syllabus and quiz engines. First pass: `json.loads(text.strip())` — handles well-formed JSON responses. Second pass: `re.search(r'\{.*\}', text, re.DOTALL)` — the `re.DOTALL` flag makes `.` match newlines, so multi-line JSON objects embedded in markdown fences are captured by the greedy `.*`. If both fail, it returns `{}` — the caller handles the empty dict with fallback logic.

---

**Q: What is the `lifespan` function in `main.py`?**

> An async context manager registered with FastAPI's `lifespan` parameter. On startup (before the first request is handled), it calls `await session_service.init_db()` to create ADK's session tables in SQLite. The `try/except AttributeError` handles older ADK versions that don't have this method. On shutdown, it yields control back (no explicit cleanup needed since SQLite and SQLAlchemy manage their own connections).

---

## 15. Comparison & Alternative Questions

---

**Q: How does this compare to existing platforms like Coursera or Khan Academy?**

> Coursera and Khan Academy have fixed, pre-written courses designed by human instructors. This project generates a dynamic, personalized curriculum on-the-fly based on the user's stated subject and skill level. The AI tutor responds to free-form questions in real time, adapts the syllabus based on quiz performance, and generates targeted remedial content — none of which is possible with pre-recorded video courses.

---

**Q: How is this different from using ChatGPT directly?**

> ChatGPT has no persistent curriculum, no structured progress tracking, no mandatory assessment, and no adaptive remediation. Every ChatGPT conversation starts fresh. This project adds: persistent syllabus stored in DB, multi-agent specialist routing, DB-enforced quiz gatekeeping, automatic remedial module injection, and session persistence across reconnects.

---

**Q: What alternative agent frameworks could be used instead of Google ADK?**

> LangChain (with LangGraph for multi-agent), LlamaIndex, AutoGen (Microsoft), CrewAI, or Semantic Kernel. Google ADK was chosen because it has native Gemini integration, first-class `transfer_to_agent` routing, and a `DatabaseSessionService` that persists conversation state — all needed features available out of the box.

---

**Q: What are alternatives to WebSocket for real-time chat?**

> Server-Sent Events (SSE) — server pushes, but unidirectional (client sends via separate HTTP). HTTP long-polling — high latency. gRPC streaming — bi-directional but complex setup. WebSocket is the industry standard for interactive chat because it is bidirectional, low-latency, and well-supported in browsers and Python frameworks.

---

**Q: Why not use Firebase or Supabase for the backend?**

> Firebase/Supabase provide managed backends but introduce vendor lock-in, require paid tiers for production scale, and abstract away the database layer (making it harder to show deep technical knowledge in an exam context). SQLite + FastAPI + SQLAlchemy gives full control and demonstrates understanding of all layers.

---

**Q: Could this project be built as a mobile app?**

> Yes. The FastAPI backend is already a REST + WebSocket API. A React Native or Flutter frontend could communicate with the same endpoints. The WebSocket protocol works identically on mobile. The main change would be building a new mobile UI that consumes the existing API.

---

## 16. Future Work & Improvements

---

**Q: What is the biggest technical improvement you would make?**

> Replacing the in-memory quiz history with server-side storage to handle browser crashes mid-quiz. A `quiz_sessions` table with `{session_id, question_index, history_json, status}` would allow resuming from exactly where the user was. This would also enable analytics on quiz performance over time.

---

**Q: How would you add user progress analytics?**

> A dedicated `quiz_results` table logging `{user_id, session_id, topic, score, wrong_topics[], timestamp}` for every completed quiz. A dashboard endpoint could then aggregate: overall pass rate, most-failed topics, average score per module, and learning velocity. The `interactions` table already logs all chat turns and could be used for engagement metrics.

---

**Q: How would you add support for multiple simultaneous learning paths?**

> The DB already supports multiple `learning_paths` rows per user (they're listed in the Sidebar). The main change would be: (1) allow multiple active WebSocket sessions simultaneously, (2) add a way to switch between active sessions without losing the current stream, and (3) ensure quiz locks are per-session (they already are via `session_id`).

---

**Q: How would you add voice input/output?**

> Frontend: Web Speech API (`SpeechRecognition`) for voice-to-text input, `SpeechSynthesis` for text-to-speech output. Backend: no changes needed — the WebSocket payload is still text. Streamed chunks could be fed to `SpeechSynthesis.speak()` as they arrive, giving real-time spoken responses.

---

**Q: How would you add collaborative learning (multiple users, same session)?**

> This would require a significant architectural change: (1) broadcasting WebSocket messages to all users in a session (requires a pub/sub system like Redis Pub/Sub), (2) conflict resolution for quiz answers (aggregate votes?), and (3) a separate `session_participants` table. The current single-user-per-session model would need to be replaced with a room-based model.

---

**Q: How would you make the quiz smarter over time?**

> Use the `quiz_results` history to build a user knowledge graph. Topics consistently failed by a user get higher quiz weight in future sessions. Topics passed with high scores get fewer review questions. This is Spaced Repetition System (SRS) logic — the same algorithm used by Anki. The LLM prompt for question generation would include the user's historical performance on each topic.

---

**Q: What monitoring would you add in production?**

> (1) Structured logging with Loguru or Python's `logging` module, sending to a centralized log aggregator. (2) Sentry for exception tracking and LLM error monitoring. (3) Prometheus + Grafana for metrics: request latency, WebSocket connection count, LLM token usage, quiz pass rates. (4) Health check endpoint `GET /health` for uptime monitoring. (5) Database query timing to detect slow queries.

---
