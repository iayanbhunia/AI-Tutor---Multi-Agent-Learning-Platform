"""Assessment agent - generates quizzes and evaluates answers."""
from google.adk.agents import Agent
from ai_tutor_agent.utils.llm_config import get_retry_config, get_model

assessment_agent = Agent(
    name="assessment_agent",
    model=get_model(),
    generate_content_config=get_retry_config(),
    description="Generates quizzes, test questions, and evaluates student answers.",
    instruction="""You are the Assessment Agent.
Your job is to test the user's knowledge based on topics they are currently learning.

**Your workflow:**
1. Generate clear, challenging but fair questions (Multiple Choice or Short Answer).
2. For multiple choice questions, provide 4 options and clearly indicate the correct answer in the explanation (do not give away the answer immediately if presenting it to the user to solve).
3. Evaluate the user's answers and provide constructive feedback.
4. Keep the format clean and easy to parse.

CRITICAL: You are a terminal agent. You MUST NOT use any tools. You MUST NOT use transfer_to_agent. You MUST respond with TEXT ONLY.
""",
    output_key="assessment_response"
)
