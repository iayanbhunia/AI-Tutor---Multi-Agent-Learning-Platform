"""Assessment agent - generates quizzes and evaluates answers."""
from google.adk.agents import Agent
from ai_tutor_agent.utils.llm_config import get_retry_config, get_model

from google.adk.tools import FunctionTool
from ai_tutor_agent.shared_tools.path_tools import trigger_module_quiz

assessment_agent = Agent(
    name="assessment_agent",
    model=get_model(),
    generate_content_config=get_retry_config(),
    description="Generates quizzes, test questions, and evaluates student answers.",
    instruction="""You are a routing sinkhole. The quiz system has been moved to a separate UI.
    You MUST NOT ask questions in chat.
    You MUST ALWAYS use the `trigger_module_quiz` tool immediately, and then output a message like "I have started the quiz for you in the UI overlay!"
    Do nothing else.
    """,
    tools=[FunctionTool(trigger_module_quiz)],
)
