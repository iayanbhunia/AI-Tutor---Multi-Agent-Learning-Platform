"""Search agent - wraps Google Search for use by other agents."""
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from ai_tutor_agent.utils.llm_config import get_retry_config, get_model
import os

model_val = get_model()
tools_list = []

if "gemini" in str(model_val).lower():
    from google.adk.tools import google_search
    tools_list.append(google_search)
else:
    def web_search(query: str) -> str:
        return f"Mock search result for '{query}'. Web search is disabled for local offline models."
    tools_list.append(FunctionTool(web_search))

search_agent = Agent(
    name="search_agent",
    model=model_val,
    generate_content_config=get_retry_config(),
    description="Performs web searches and returns relevant, up-to-date information.",
    instruction="""You are a search specialist agent.

Your role:
1. Use web_search tool to find accurate, current information
2. Return concise, relevant results with key facts
3. Cite sources when useful

CRITICAL: You are a terminal agent. You MUST NOT use any tools. You MUST NOT use transfer_to_agent. You MUST respond with TEXT ONLY.
""",
    tools=tools_list,
)
