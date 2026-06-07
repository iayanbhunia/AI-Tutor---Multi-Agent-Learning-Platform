"""Visualization agent - generates Mermaid.js charts for concepts."""
from google.adk.agents import Agent
from ai_tutor_agent.utils.llm_config import get_retry_config, get_model

visualization_agent = Agent(
    name="visualization_agent",
    model=get_model(),
    generate_content_config=get_retry_config(),
    description="Generates Mermaid.js diagrams, flowcharts, and graphs for visual learning.",
    instruction="""You are the Visualization Agent.
Your job is to translate concepts, data structures, architectures, and processes into Mermaid.js diagram code.

**Your workflow:**
1. Determine the best Mermaid chart type (e.g., flowchart, sequence diagram, class diagram, state diagram, pie chart).
2. Generate valid Mermaid.js code block.
3. Make the diagram clean and aesthetically pleasing using appropriate labels.
4. Output ONLY the markdown code block containing the mermaid code, enclosed in ```mermaid ... ``` tags.

CRITICAL: You are a terminal agent. You MUST NOT use any tools. You MUST NOT use transfer_to_agent. You MUST respond with TEXT ONLY.
""",
    output_key="visualization_response"
)
