# 🎓 AI Tutor — Multi-Agent Intelligent Tutoring System

> A personalized, real-time AI tutor powered by a hierarchical multi-agent system, enforced mastery quizzes, and adaptive remediation. Built for any subject, any skill level.

---

## 📖 What Is This?

The **AI Tutor** is a full-stack educational platform designed as a Final Year CSE project. It goes far beyond a simple AI chatbot — it is a structured **Intelligent Tutoring System (ITS)** that:

- 🗺️ **Generates a personalized curriculum** on-the-fly from a multi-turn onboarding conversation
- 🤖 **Routes each query** to the most appropriate specialist agent (theory, coding, math, visualization, search, assessment)
- 📝 **Enforces mandatory quizzes** at 5 independent layers — LLM prompt, WebSocket protocol, database flag, API tool, and UI lock — making bypass structurally impossible
- 🧩 **Injects targeted remedial modules** into the live syllabus for each subtopic answered incorrectly (one module per wrong answer)
- 📊 **Renders inline Mermaid.js diagrams** for visual explanation of complex concepts
- 💬 **Streams responses in real time** via WebSocket with token-by-token delivery
- 🔒 **Persists quiz state to the database** — survives page refreshes and browser crashes
- 🖥️ **Supports fully offline usage** via Ollama local LLMs — no API key required

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────┐
│         React Frontend (Vite)           │
│  Auth · Onboarding · Chat · Quiz · Sidebar│
└────────────────┬────────────────────────┘
                 │ REST + WebSocket
┌────────────────▼────────────────────────┐
│        FastAPI Backend (:8000)          │
│  REST API · WebSocket Handler · DB Layer│
│  syllabus_engine · quiz_engine          │
└────────────────┬────────────────────────┘
                 │ ADK run_async()
┌────────────────▼────────────────────────┐
│       Google ADK Agent Layer            │
│  root_agent (orchestrator)              │
│  theory · coding · math · viz           │
│  search · assessment                    │
└────────────────┬────────────────────────┘
                 │ LLM API
┌────────────────▼────────────────────────┐
│  Google Gemini API  │  Ollama (local)   │
└─────────────────────────────────────────┘
```

For a detailed breakdown of every component, data model, and API endpoint, see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 🧰 Tech Stack

### Backend
| Package | Version | Purpose |
|---|---|---|
| `google-adk` | 1.33.0 | Multi-agent orchestration framework |
| `fastapi` | 0.124.4 | Async REST + WebSocket backend |
| `uvicorn` | 0.33.0 | ASGI server |
| `litellm` | 1.87.1 | Universal LLM proxy (Gemini, Ollama, OpenAI) |
| `SQLAlchemy` | 2.0.44 | ORM + SQLite WAL mode |
| `aiosqlite` | 0.22.1 | Async SQLite driver for ADK session service |
| `python-multipart` | 0.0.27 | FastAPI form + file upload support |
| `pydantic` | 2.13.4 | Request/response validation models |
| `python-dotenv` | 1.2.1 | `.env` file loading |

### Frontend
| Package | Purpose |
|---|---|
| `react` + `react-dom` v19 | UI framework |
| `vite` v8 | Build tool & dev server |
| `typescript` | Type safety |
| `tailwindcss` v4 | Utility-first styling |
| `zustand` | Lightweight global state management |
| `react-markdown` | Renders AI markdown responses |
| `remark-gfm` | GitHub Flavored Markdown (tables, strikethrough) |
| `remark-breaks` | Converts newlines to `<br>` in markdown |
| `lucide-react` | Icon library |
| `mermaid` | Diagram spec (used server-side via mermaid.ink) |

### Infrastructure
| Tool | Purpose |
|---|---|
| **Google Gemini API** | Default cloud LLM (Gemini 2.5 Flash) |
| **Ollama** | Local LLM runtime (Llama 3.1, Mistral, etc.) |
| **SQLite (WAL mode)** | Persistent storage — users, syllabuses, chat history |

---

## 🚀 Installation & Setup

### Prerequisites

Ensure you have these installed before starting:

| Requirement | Version | Check Command |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | Any | `git --version` |

You also need **one of** the following LLM backends:
- **Google Gemini API key** — get one free at [aistudio.google.com](https://aistudio.google.com)
- **Ollama** (for offline use) — download from [ollama.com](https://ollama.com)

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/bhaskar966/AI-Tutor.git
cd AI-Tutor
```

---

### Step 2 — Python Virtual Environment & Backend Dependencies

Create and activate a virtual environment (**required** to isolate dependencies):

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

You should see `(.venv)` at the start of your terminal prompt.

Install backend dependencies:
```bash
pip install -r requirements.txt
```

---

### Step 3 — Environment Variables

Create a `.env` file inside the `ai_tutor_agent/` directory:

```bash
# macOS/Linux
touch ai_tutor_agent/.env

# Windows
type nul > ai_tutor_agent\.env
```

Then open it and add your configuration:

The project uses a **single `.env` file** in the repo root with all configuration:

```ini
# .env  (repo root — already exists, edit this file)

# Cloud model (used when ACTIVE_MODE=online)
ONLINE_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here

# Local model (used when ACTIVE_MODE=local)
LOCAL_MODEL=ollama_chat/llama3.1

# ← THE SWITCH: set to "online" or "local"
ACTIVE_MODE=local

# Database location (auto-created on first run)
DATABASE_URI=sqlite:///ai_tutor.db
```

> **Switching modes**: Change `ACTIVE_MODE=local` to `ACTIVE_MODE=online` (or vice versa) and restart the backend.

If you don't have a Gemini API key yet, get one free at [aistudio.google.com](https://aistudio.google.com).


---

### Step 4 — Frontend Dependencies

Navigate to the `frontend/` directory and install npm packages:

```bash
cd frontend
npm install
cd ..
```

This installs all required packages including `react-markdown`, `remark-gfm`, `remark-breaks`, `zustand`, `lucide-react`, and TailwindCSS v4.

---

### Step 5 — (Ollama only) Pull a Model

If using Ollama, pull a model first (one-time, ~4–8 GB download):

```bash
# Recommended — good balance of speed and quality
ollama pull llama3.1

# Lighter alternative (~4 GB)
ollama pull mistral

# Larger, more capable model (~20 GB)
ollama pull llama3.1:70b
```

Ensure Ollama is running in the background before starting the backend.

---

## 🏃 Running the Application

You need **two terminal windows** running simultaneously.

### Terminal 1 — Backend (FastAPI + ADK Agents)

From the project root `AI-Tutor/`, with your virtual environment active:

```bash
# Activate venv if not already active
# macOS/Linux: source .venv/bin/activate
# Windows:     .\.venv\Scripts\activate

uvicorn fastapi_app.main:app --reload --port 8000
```

The backend starts at **`http://localhost:8000`**. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Terminal 2 — Frontend (React + Vite Dev Server)

From the `frontend/` directory:

```bash
cd frontend
npm run dev
```

The frontend starts at **`http://localhost:5173`**. Open this in your browser.

> **Production build**: If you want to serve the frontend from FastAPI directly (single port), run `npm run build` in the `frontend/` directory. FastAPI mounts the built `dist/` as static files and serves everything from port 8000.

---

## 📁 Project Structure

```
AI-Tutor/
├── ai_tutor_agent/               # Google ADK agent package
│   ├── agent.py                  # Root orchestrator agent
│   ├── adk.yaml                  # ADK application config
│   ├── .env                      # ← YOUR CONFIG FILE GOES HERE
│   ├── shared_tools/             # FunctionTools shared across agents
│   │   ├── db_tools.py           # History, quiz enforcement tools
│   │   └── path_tools.py         # Syllabus + trigger_quiz tools
│   ├── subagents/                # 6 specialist agents
│   │   ├── assessment_agent/
│   │   ├── coding_agent/
│   │   ├── math_agent/
│   │   ├── theory_agent/
│   │   ├── visualization_agent/
│   │   └── search_agent/
│   └── utils/
│       ├── db_manager.py         # SQLAlchemy singleton (WAL mode)
│       └── llm_config.py         # Gemini vs LiteLLM model selector
│
├── fastapi_app/
│   ├── main.py                   # All REST endpoints + WebSocket handler
│   ├── quiz_engine.py            # 5-question adaptive quiz via litellm
│   └── syllabus_engine.py        # Multi-turn onboarding via litellm
│
├── frontend/                     # React + Vite SPA
│   ├── src/
│   │   ├── App.tsx               # Root component + auth guard
│   │   ├── store/store.ts        # Zustand global state
│   │   └── components/
│   │       ├── AuthView.tsx
│   │       ├── OnboardingModal.tsx
│   │       ├── Sidebar.tsx
│   │       ├── ChatInterface.tsx  # WebSocket chat + streaming
│   │       ├── QuizOverlay.tsx    # Full-screen quiz modal
│   │       └── UserProfile.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── ai_tutor.db                   # SQLite database (auto-created)
├── requirements.txt              # Python dependencies
├── requirements-freeze.txt       # Full pinned dependency snapshot
├── ARCHITECTURE.md               # Deep-dive system documentation
├── QNA.md                        # 150+ Q&A for project presentations
├── COMPARATIVE_STUDY.md          # Academic literature review
└── PROJECT_REPORT.md             # Final year project report
```

---

## 🔀 Switching Between Cloud & Local LLM

All switching is done through **`ACTIVE_MODE`** in the root `.env` file. You configure both models once, then just flip the switch:

```ini
# .env
ONLINE_MODEL=gemini-2.5-flash   # cloud model to use
LOCAL_MODEL=ollama_chat/llama3.1 # local model to use
ACTIVE_MODE=local                # ← change this to switch
```

| `ACTIVE_MODE` | Model Used | Needs Internet | Notes |
|---|---|---|---|
| `online` | `ONLINE_MODEL` (e.g. `gemini-2.5-flash`) | ✅ Yes | Best quality. Needs `GEMINI_API_KEY`. |
| `local` | `LOCAL_MODEL` (e.g. `ollama_chat/llama3.1`) | ❌ No | Privacy-first. Needs Ollama running. |

**To change the specific model** used in each mode, edit `ONLINE_MODEL` or `LOCAL_MODEL` directly:

| Variable | Example values |
|---|---|
| `ONLINE_MODEL` | `gemini-2.5-flash`, `gemini-2.0-flash-lite` |
| `LOCAL_MODEL` | `ollama_chat/llama3.1`, `ollama_chat/mistral`, `ollama_chat/llama3.1:70b` |

Restart the backend after any `.env` change.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `"no such column"` DB error | Delete `ai_tutor.db` in the root directory and restart backend. It auto-recreates. |
| `WebSocket disconnected` | Ensure the backend is running on port 8000. Check `vite.config.ts` proxy settings. |
| `Connection refused` (Ollama) | Start the Ollama app. It must be running before the backend starts. Check: `ollama list` |
| `GOOGLE_API_KEY not set` | Add your API key to `ai_tutor_agent/.env`. Get one free at aistudio.google.com. |
| `npm install` fails | Ensure Node.js 18+ is installed. Try `npm install --legacy-peer-deps`. |
| Quiz permanently locked | Delete `ai_tutor.db` and restart, or run: `UPDATE learning_paths SET quiz_pending_module = NULL;` in SQLite. |
| Mermaid diagrams not rendering | The system uses the `mermaid.ink` API. Check internet connectivity (Gemini mode) or verify the diagram syntax if local. |
| `Module not found` (Python) | Ensure the virtual environment is activated (`source .venv/bin/activate`) before running uvicorn. |

---

## 📚 Documentation

| File | Description |
|---|---|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Full technical architecture, database schemas, API reference, data flow diagrams |
| [QNA.md](./QNA.md) | 150+ Q&A covering every aspect of the system for viva/presentations |
| [COMPARATIVE_STUDY.md](./COMPARATIVE_STUDY.md) | Academic literature review comparing this system to existing ITS and commercial platforms |
| [PROJECT_REPORT.md](./PROJECT_REPORT.md) | Complete final year project report (30+ pages) |

---

## 🙏 Acknowledgements

- [Google ADK](https://github.com/google/adk) — agent orchestration framework
- [FastAPI](https://fastapi.tiangolo.com/) — async backend framework
- [React](https://react.dev/) + [Vite](https://vitejs.dev/) — frontend stack
- [LiteLLM](https://docs.litellm.ai/) — universal LLM proxy
- [Ollama](https://ollama.com/) — local model runtime
- [mermaid.ink](https://mermaid.ink/) — server-side diagram rendering API
- [Zustand](https://zustand-demo.pmnd.rs/) — state management
- [react-markdown](https://github.com/remarkjs/react-markdown) + [remark-gfm](https://github.com/remarkjs/remark-gfm) — markdown rendering pipeline

---

*Final Year Project — B.Tech Computer Science & Engineering*
