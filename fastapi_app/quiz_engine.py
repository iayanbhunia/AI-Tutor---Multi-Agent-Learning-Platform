import os
import json
import litellm
import re

litellm.set_verbose = False

def _get_litellm_model():
    model = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
    # LiteLLM needs the provider prefix for gemini
    if not model.startswith("ollama/") and "/" not in model:
        return f"gemini/{model}"
    return model

def _extract_json(text: str) -> dict:
    try:
        # Try raw load first
        return json.loads(text.strip())
    except:
        # Try regex extract
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {}

def generate_first_question(syllabus: str) -> dict:
    prompt = f"""You are an expert AI Examiner.
Generate the very first quiz question to test the user based on the following syllabus.
Focus on the first foundational topic.

Syllabus:
{syllabus}

Respond strictly in JSON format, with no markdown formatting outside the braces.
{{
    "question": "What is...",
    "type": "mcq", // strictly "mcq" or "short_answer"
    "options": ["A", "B", "C", "D"], // only include this array if type is "mcq"
    "topic": "The specific topic from syllabus being tested"
}}
"""
    model = _get_litellm_model()
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content
    return _extract_json(content)

def evaluate_and_generate_next(syllabus: str, history: list, answer: str) -> dict:
    history_str = json.dumps(history, indent=2)
    prompt = f"""You are an expert AI Examiner.
The user is learning based on this syllabus: {syllabus}
Here is the quiz history so far (each item has the question and the correct answer evaluated previously, but we are evaluating their LATEST answer now):
{history_str}

The user's latest answer to the last question was: "{answer}"

Instructions:
1. Evaluate their answer. Provide short, constructive feedback.
2. If the total number of questions asked (including this one) is less than 5, generate the next question. Make it slightly harder if they were right, or easier/same level if wrong. Focus on the next topic in the syllabus if they mastered the current one.
3. If the total number of questions asked is 5 or more, provide a final review instead of a question. 
   - Indicate if they need a remedial module (if they got 2 or more wrong, or struggled heavily).
   - If they need remedial, specify the exact sub-topic they failed so it can be added to the syllabus.

Respond strictly in JSON format:
{{
    "evaluation": "Correct! Good job because...",
    "is_correct": true,
    "status": "ongoing", // strictly "ongoing" or "complete"
    "next_question": {{ // Include ONLY if status is "ongoing"
        "question": "...",
        "type": "mcq",
        "options": ["A", "B", "C", "D"],
        "topic": "..."
    }},
    "final_review": {{ // Include ONLY if status is "complete"
        "score": "4/5",
        "feedback": "Great overall, but you need to review X...",
        "needs_remedial": true, // true or false
        "remedial_topic": "Coroutines Under The Hood" // Only if needs_remedial is true
    }}
}}
"""
    model = _get_litellm_model()
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content
    return _extract_json(content)
