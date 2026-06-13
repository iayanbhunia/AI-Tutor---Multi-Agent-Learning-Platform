import asyncio
from fastapi_app.quiz_engine import generate_first_question

async def test():
    print(generate_first_question('{"syllabus": [{"module": "Test"}]}', "Test"))

asyncio.run(test())
