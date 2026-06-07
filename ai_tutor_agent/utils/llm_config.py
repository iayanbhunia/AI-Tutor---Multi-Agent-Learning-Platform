import os
from dotenv import load_dotenv

load_dotenv()

def get_model():
    """Return the correct model connector based on AGENT_MODEL env var."""
    model_name = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
    
    if model_name.startswith("ollama/"):
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model=model_name)
    elif "/" in model_name:
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model=model_name)
    else:
        return model_name

def get_retry_config():
    """Return retry config only for Gemini models. None for LiteLLM."""
    model_name = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
    if "/" not in model_name:
        from google.genai import types
        return types.GenerateContentConfig(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(initial_delay=2, attempts=15)
            )
        )
    return None
