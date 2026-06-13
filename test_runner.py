import asyncio
from ai_tutor_agent.agent import root_agent
from google.adk.sessions import DatabaseSessionService
from google.genai import types

async def main():
    service = DatabaseSessionService(db_url="sqlite+aiosqlite:///ai_tutor.db")
    # await service.init_db()  # Not needed or doesn't exist
    
    session = await service.get_session(app_name="ai_tutor", user_id="test_user", session_id="test_session")
    if not session:
        await service.create_session("ai_tutor", "test_user", "test_session", state={})
    
    from google.adk.runners import Runner
    runner = Runner(app_name="ai_tutor", agent=root_agent, session_service=service)
    
    msg = types.Content(role="user", parts=[types.Part(text="ask me a quiz related to the history of mobile development")])
    try:
        async for event in runner.run_async("test_user", "test_session", new_message=msg):
            print(f"EVENT TYPE: {type(event)}")
            print(event)
            if hasattr(event, "tool_calls") and event.tool_calls:
                for tc in event.tool_calls:
                    print(f"TOOL CALL: {tc.name}, Args: {getattr(tc, 'args', None)}")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(main())
