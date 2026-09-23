import os
from typing import Optional
from groq import Groq

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = Groq(api_key=api_key)
    return _client


def chat(
    system_prompt: str,
    user_prompt: str,
    model: str = "llama-3.1-8b-instant",
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    client = get_client()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content or ""
