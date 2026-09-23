import os
from typing import Optional
from cerebras.cloud.sdk import Cerebras

_client: Optional[Cerebras] = None


def get_client() -> Cerebras:
    global _client
    if _client is None:
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise RuntimeError("CEREBRAS_API_KEY is not set")
        _client = Cerebras(api_key=api_key)
    return _client


def chat(
    system_prompt: str,
    user_prompt: str,
    model: str = "llama3.1-8b",
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
        max_completion_tokens=max_tokens,
    )
    return completion.choices[0].message.content or ""
