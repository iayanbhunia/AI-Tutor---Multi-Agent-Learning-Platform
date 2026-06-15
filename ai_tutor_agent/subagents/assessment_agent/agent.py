"""Assessment agent - generates quizzes and evaluates answers."""
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import os

from ai_tutor_agent.utils.llm_config import get_retry_config, get_model
from ai_tutor_agent.shared_tools.path_tools import trigger_topic_quiz

assessment_agent = Agent(
    name="assessment_agent",
    description="Specialist in executing quizzes. Route here ONLY to start a quiz. Do NOT route here to teach topics or explain concepts.",
    model=get_model(),
    generate_content_config=get_retry_config(),
    instruction="""You are the Assessment Specialist.
    CRITICAL RULE: Check the user's message first!
    - IF the user's message starts with `[System Action]`, you MUST NOT call any tools. You must ONLY output the exact text: "Quiz sequence finished. Returning to tutor."
    - OTHERWISE, your ONLY job is to trigger the interactive quiz overlay using the `trigger_topic_quiz` tool. You must use the tool immediately, and then output a message like "I have started the quiz for you in the UI overlay!"
    
    Do not ask questions. Do not conduct the quiz in the chat.

    ABSOLUTE RULE:
    - ALWAYS use the actual `trigger_topic_quiz` tool or python function provided in your environment. NEVER type out raw JSON strings like `{"action": "trigger_topic_quiz"}` or `{"id": "call_..."}` in your text response.
    """,
    tools=[FunctionTool(trigger_topic_quiz)],
)
