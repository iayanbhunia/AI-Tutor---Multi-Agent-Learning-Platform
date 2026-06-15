import os
from dotenv import load_dotenv

load_dotenv()

def get_model_name():
    """Helper to get the current model string based on ACTIVE_MODE."""
    mode = os.getenv("ACTIVE_MODE", "online")
    if mode == "online":
        return os.getenv("ONLINE_MODEL", "gemini-2.5-flash")
    return os.getenv("LOCAL_MODEL", "ollama/llama3")

def get_model():
    """Return the correct model connector based on ACTIVE_MODE env var."""
    model_name = get_model_name()
    
    if model_name.startswith("ollama/") or "/" in model_name:
        from google.adk.models.lite_llm import LiteLlm, _ensure_litellm_imported
        import litellm
        _ensure_litellm_imported()
        class LocalToolLiteLlm(LiteLlm):
            async def generate_content_async(self, llm_request, stream=False, **kwargs):
                full_text = ""
                is_json_tool = None  # None=undecided, True=tool call (buffer), False=text (stream)

                async for chunk in super().generate_content_async(llm_request, stream=stream, **kwargs):
                    text = ""
                    try:
                        for candidate in chunk.candidates:
                            for part in candidate.content.parts:
                                if getattr(part, 'text', None):
                                    text = part.text
                                    full_text += text
                    except Exception:
                        pass

                    # Make the streaming-vs-buffering decision exactly once,
                    # on the first chunk that contains text.
                    if is_json_tool is None and full_text.strip():
                        stripped = full_text.strip()
                        if stripped == "{" or stripped.startswith('{"name"'):
                            is_json_tool = True   # Tool call JSON — buffer silently
                        else:
                            is_json_tool = False  # Normal text — stream immediately

                    if is_json_tool is True:
                        continue  # Still buffering — don't yield yet

                    # is_json_tool is False, or still None (no text in chunk yet)
                    yield chunk  # Stream this chunk immediately to the WebSocket

                # After the full response: if it was a tool call, parse and emit as FunctionCall
                if is_json_tool is True:
                    try:
                        import json
                        from google.genai.types import FunctionCall, Part, GenerateContentResponse, Candidate, Content
                        data = json.loads(full_text.strip())
                        name = data.get("name")
                        args = data.get("parameters", {})
                        if name:
                            fc_part = Part(function_call=FunctionCall(name=name, args=args))
                            yield GenerateContentResponse(
                                candidates=[Candidate(content=Content(parts=[fc_part], role="model"))]
                            )
                    except Exception as e:
                        print("Local tool parse error:", e)
                        from google.genai.types import Part, GenerateContentResponse, Candidate, Content
                        yield GenerateContentResponse(
                            candidates=[Candidate(content=Content(parts=[Part(text=full_text)], role="model"))]
                        )

        return LocalToolLiteLlm(model=model_name)
    else:
        return model_name

def get_streaming_model():
    """Return the model connector with streaming enabled for specialist agents."""
    return get_model()

def get_retry_config():
    """Return retry config only for Gemini models. None for LiteLLM."""
    model_name = get_model_name()
    if "/" not in model_name:
        from google.genai import types
        return types.GenerateContentConfig(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(initial_delay=2, attempts=15)
            )
        )
    return None

def switch_all_agents_model(mode: str):
    """
    Dynamically switches the model for all running ADK agents
    and persists the setting in .env
    """
    # 1. Update ENV file to persist
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        found = False
        for i, line in enumerate(lines):
            if line.startswith("ACTIVE_MODE="):
                lines[i] = f"ACTIVE_MODE={mode}\n"
                found = True
                break
        
        if not found:
            lines.append(f"ACTIVE_MODE={mode}\n")
            
        with open(env_path, "w") as f:
            f.writelines(lines)
    else:
        with open(env_path, "w") as f:
            f.write("ONLINE_MODEL=gemini-2.5-flash\n")
            f.write("LOCAL_MODEL=ollama/llama3\n")
            f.write(f"ACTIVE_MODE={mode}\n")
            
    # 2. Update current environment
    os.environ["ACTIVE_MODE"] = mode
    
    # 3. Reload models in running ADK agents
    new_model_instance = get_model()
    from ai_tutor_agent.agent import root_agent
    
    def set_model_recursive(agent, m):
        agent.model = m
        for sub in getattr(agent, 'sub_agents', []) or []:
            set_model_recursive(sub, m)
            
    set_model_recursive(root_agent, new_model_instance)
