# 🎓 AI Tutor System - Final Year CSE Project

> **Your personal, AI-powered mentor for DSA, System Design, and Development.**

![Tutor Dashboard Placeholder](https://github.com/bhaskar966/AI-Tutor/blob/master/images/AI_Tutor_Learning_Path.png?raw=true)

## 📖 Introduction

This repository contains the source code for our **Final Year Computer Science and Engineering (CSE) Project**. 

The **AI Tutor System** is a sophisticated, real-time multi-agent educational platform. It goes beyond simple chatbots by providing dynamic, personalized learning paths, interactive lessons, and automated module checkpoints. It is designed to act as a personal tutor across three main domains:
*   **DSA (Data Structures & Algorithms)**: Master algorithmic thinking and problem-solving.
*   **System Design**: Learn to architect scalable and robust systems.
*   **Development**: Hands-on coding guidance for Web, Mobile, and Backend technologies.

## 🏗️ Architecture Overview

The project follows a modern client-server architecture powered by a multi-agent intelligence core:
*   **Frontend**: React + Vite application for a highly responsive, real-time chat interface.
*   **Backend**: FastAPI serving REST endpoints and WebSockets for real-time streaming.
*   **Agent Core**: Hierarchical multi-agent system powered by the Google Agent Development Kit (ADK).
*   **Database**: SQLite with SQLAlchemy for persistent user profiles, syllabuses, and chat histories.

For a deep dive into the system design, database schemas, and data flow, please see our detailed [ARCHITECTURE.md](./ARCHITECTURE.md).

## 🧰 3rd Party Resources & Technologies

This project leverages several cutting-edge third-party frameworks and tools:
*   **[Google ADK (Agent Development Kit)](https://github.com/google/adk)**: The core framework for orchestrating the multi-agent system.
*   **[FastAPI](https://fastapi.tiangolo.com/)**: High-performance asynchronous backend framework.
*   **[React](https://react.dev/) & [Vite](https://vitejs.dev/)**: For a blazingly fast frontend UI.
*   **[TailwindCSS](https://tailwindcss.com/) & [Zustand](https://zustand-demo.pmnd.rs/)**: Frontend styling and global state management.
*   **[LiteLLM](https://docs.litellm.ai/)**: Universal LLM proxy allowing seamless switching between Google Gemini and local models.
*   **[Ollama](https://ollama.com/)** *(Optional but Recommended)*: For running local, privacy-first open-source language models like Llama 3.1.
*   **[Mermaid.js](https://mermaid.js.org/)**: For rendering dynamic flowcharts and architecture diagrams in the chat.

---

## 🚀 Installation & Setup

### Prerequisites

Before you begin, ensure you have the following installed on your system:
1.  **Python 3.10+**: Required for the backend and AI agents.
2.  **Node.js 18+ & npm**: Required for running the React frontend.
3.  **Google Gemini API Key** OR **Ollama installed locally** (instructions below).

### 1. Clone the Repository

```bash
git clone https://github.com/bhaskar966/AI-Tutor.git
cd AI-Tutor
```

### 2. Backend Setup & Virtual Environment (CRITICAL)

You **must** create and activate a Python virtual environment to prevent dependency conflicts.

Open a terminal in the root `AI-Tutor` directory and run:

**For Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**For macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

*(You should see `(.venv)` appear at the beginning of your terminal prompt, indicating it is active.)*

With the virtual environment active, install the Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables (.env)

Create a file named `.env` in the `ai_tutor_agent` directory (`ai_tutor_agent/.env`). Add the following configuration. We recommend using Ollama for local execution:

```ini
# Database Configuration
DATABASE_URI=sqlite:///ai_tutor.db

# LLM Configuration: Using Local Ollama
AGENT_MODEL=ollama/llama3.1
```

### 4. Frontend Setup

Open a **new terminal window** and navigate to the `frontend` directory.

```bash
cd frontend
npm install
```

---

## 🏃‍♂️ Running the Application Locally

To run the application with the local Ollama model, you will need **two separate terminal windows**. Ensure you have downloaded Ollama from [ollama.com](https://ollama.com/) and it is running in the background.

Pull the `llama3.1` model (only needs to be done once):
```bash
ollama pull llama3.1
```
*(The backend natively connects to Ollama via `litellm` without requiring a separate proxy server).*

### Terminal 1: Start the FastAPI Backend
Open a terminal, navigate to the `AI-Tutor` root directory, **activate your virtual environment**, and start the backend:
```bash
# macOS/Linux: source .venv/bin/activate
# Windows: .\.venv\Scripts\activate

uvicorn fastapi_app.main:app --reload --port 8000
```
*The backend API will be available at `http://localhost:8000`*

### Terminal 2: Start the React Frontend
Open a new terminal, navigate to the `frontend` directory, and start the UI:
```bash
cd frontend
npm run dev
```
*The frontend will start a local dev server, typically at `http://localhost:5173`*

Open your browser and navigate to `http://localhost:5173` to start using the AI Tutor!

---

## 🛠️ Debugging & Troubleshooting

*   **Database Issues**: If you experience schema errors (e.g., "no such column"), delete the `ai_tutor.db` file in the root directory. It will automatically recreate itself on the next run.
*   **WebSocket Disconnections**: Ensure your backend is running on the correct port and the frontend proxy in `vite.config.ts` matches the backend port.
*   **Ollama Connection Refused**: Ensure the Ollama application is running on your machine (usually visible in your system tray or menu bar) before interacting with the chat.

## 🙏 Acknowledgements

A special thanks to the faculty and mentors supporting our Final Year CSE project, and to the open-source communities behind ADK, FastAPI, and React.
