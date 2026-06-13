import asyncio
import os
import json
from ai_tutor_agent.agent import root_agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ai_tutor.db'))
    adk_db_url = f"sqlite+aiosqlite:///{db_path}"
    
    session_service = DatabaseSessionService(db_url=adk_db_url)
    
    user_id = "debug_user"
    session_id = "debug_session"
    
    await session_service.create_session(
        app_name="ai_tutor", 
        user_id=user_id, 
        session_id=session_id, 
        state={"current_user_id": user_id, "session_id": session_id, "authenticated": True}
    )
    
    runner = Runner(app_name="ai_tutor", agent=root_agent, session_service=session_service)
    
    prompt = "can you create an image of a function machine"
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    print("Sending prompt to runner...")
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
            print(f"Event type: {type(event)}")
            if hasattr(event, 'get_function_calls'):
                calls = event.get_function_calls()
                if calls:
                    for call in calls:
                        print(f"Tool call: {call.name}({call.args})")
            
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"Chunk: {part.text}")
    except Exception as e:
        print(f"Error: {e}")
        
    print("\nSending follow up...")
    prompt = "can you create an image again"
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
            print(f"Event type: {type(event)}")
            if hasattr(event, 'get_function_calls'):
                calls = event.get_function_calls()
                if calls:
                    for call in calls:
                        print(f"Tool call: {call.name}({call.args})")
            
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"Chunk: {part.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
