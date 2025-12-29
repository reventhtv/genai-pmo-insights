import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(prompt: str):
    """
    Calls the LLM and expects STRICT JSON output.
    Returns None if the call fails or output is invalid.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception:
        return None
