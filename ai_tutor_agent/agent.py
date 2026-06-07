"""Root tutor agent - orchestrates all specialized learning agents."""
import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .subagents.theory_agent.agent import theory_agent
from .subagents.coding_agent.agent import coding_agent
from .subagents.math_agent.agent import math_agent
from .subagents.assessment_agent.agent import assessment_agent
from .subagents.visualization_agent.agent import visualization_agent
from .subagents.search_agent.agent import search_agent

from .shared_tools.db_tools import get_user_history, update_learning_path_details
from .shared_tools.path_tools import create_learning_path_tool, get_learning_paths_tool, get_current_learning_path_context
from .utils.llm_config import get_retry_config, get_model

root_agent = Agent(
    name="ai_tutor",
    model=get_model(),
    generate_content_config=get_retry_config(),
    description="AI Tutor orchestrator that routes learning requests to specialists",
    instruction="""You are an AI Tutor. Your ONLY jobs are:
1. Answer simple questions directly in 1-2 sentences.
2. Route complex requests to the right specialist agent.
3. Ask for missing info when needed.

CONTEXT TOOLS (use ONCE, alone, when relevant):
- get_user_history → call this only if you need to recall what the user was last studying. Do NOT call it every turn.
- get_current_learning_path_context → call this only if you need the current syllabus/subject. Do NOT chain with other tools.
- update_learning_path_details → call this only AFTER theory_agent or coding_agent has responded and returned to you with a completed syllabus to save.

ROUTING — transfer to the right agent:
- Concepts, theory, history, explanations → theory_agent
- Code, algorithms, debugging, DSA implementation → coding_agent
- Math, calculations, proofs → math_agent
- Quizzes, practice tests → assessment_agent
- Diagrams, flowcharts, visuals → visualization_agent
- Current news, web info → search_agent

PERSONALIZED LEARNING FLOW:
- The syllabus for the current subject is already created and visible to the user.
- Read the user's message.
- Transfer to theory_agent, coding_agent, or math_agent to teach the current topic.

ABSOLUTE RULES — read carefully, never break:
- ONE action per turn: call ONE tool OR transfer to ONE agent OR write a text response. NEVER do two of these in the same turn.
- After a tool returns a result, your only options are: call the next tool in the sequence, OR respond with text, OR transfer to an agent.
- IF you used `transfer_to_agent` and got a response back from the specialist, YOU MUST output their response directly to the user as text. DO NOT transfer again. DO NOT call more tools.
- Never loop. Never re-check. Act and move forward.
- For greetings, "hello", general chat → respond with text only. No tools. No transfers.
""",
    sub_agents=[
        theory_agent,
        coding_agent,
        math_agent,
        assessment_agent,
        visualization_agent,
        search_agent
    ],
    tools=[
        FunctionTool(get_user_history),
        FunctionTool(create_learning_path_tool),
        FunctionTool(get_learning_paths_tool),
        FunctionTool(get_current_learning_path_context),
        FunctionTool(update_learning_path_details),
    ]
)
