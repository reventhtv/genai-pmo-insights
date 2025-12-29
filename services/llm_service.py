import os
import json
from openai import OpenAI


def call_llm(prompt: str):
    """
    Calls the LLM if API key is available.
    Returns None if key is missing or call fails.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None  # Graceful fallback

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception:
        return None
