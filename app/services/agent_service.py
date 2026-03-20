import os
import json
import logging

logger = logging.getLogger(__name__)

_SYSTEM = "You generate structured payment intents for financial agents."
_PROMPT = """Convert the following task into a payment JSON.

Task:
{task}

Return ONLY valid JSON in this format:

{{
  "recipient": "string",
  "amount": number,
  "purpose": "string"
}}"""


def _parse_json(content: str) -> dict:
    content = content.strip()
    # Strip markdown code fences if present
    if "```" in content:
        parts = content.split("```")
        content = parts[1] if len(parts) > 1 else parts[0]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def generate_payment_intent(task: str) -> dict:
    # Try Anthropic (hackathon / SYNTH_API_KEY)
    synth_key = os.getenv("SYNTH_API_KEY")
    if synth_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=synth_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=_SYSTEM,
                messages=[{"role": "user", "content": _PROMPT.format(task=task)}],
            )
            return _parse_json(message.content[0].text)
        except json.JSONDecodeError as e:
            logger.error("Anthropic response was not valid JSON: %s", e)
            return {"error": "AI response was not valid JSON"}
        except Exception as e:
            logger.error("Anthropic request failed: %s — falling back to OpenAI", e)

    # Fallback: OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": _PROMPT.format(task=task)},
                ],
                temperature=0,
            )
            return _parse_json(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "AI response was not valid JSON"}
        except Exception as e:
            logger.error("OpenAI request failed: %s", e)
            return {"error": "AI request failed", "details": str(e)}

    # Demo fallback
    logger.warning("No AI API key configured — returning demo response")
    return {"recipient": "demo-vendor", "amount": 0, "purpose": task, "mode": "demo"}
