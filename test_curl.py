import requests
import asyncio

url = "http://localhost:8000/api/quiz/start"
payload = {"user_id": "test_user", "session_id": "test_session", "module_name": "Test Module"}
headers = {"Content-Type": "application/json"}
try:
    res = requests.post(url, json=payload)
    print(res.status_code, res.text)
except Exception as e:
    print(e)
