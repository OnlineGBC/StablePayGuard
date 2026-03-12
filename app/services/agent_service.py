import os
import json
from openai import OpenAI


def generate_payment_intent(task: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "error": "OPENAI_API_KEY not configured",
            "recipient": "demo-vendor",
            "amount": 0,
            "purpose": task
        }

    client = OpenAI(api_key=api_key)

    prompt = f"""
Convert the following task into a payment JSON.

Task:
{task}

Return ONLY valid JSON in this format:

{{
  "recipient": "string",
  "amount": number,
  "purpose": "string"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You generate structured payment intents for financial agents."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "AI response was not valid JSON",
                "raw_response": content
            }

    except Exception as e:
        return {
            "error": "OpenAI request failed",
            "details": str(e)
        }
