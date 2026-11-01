"""LLM client: the only module that knows which LLM provider we use."""

import httpx
import ollama


class LLMError(RuntimeError):
    """The LLM could not produce an answer (server down, model missing, timeout)."""


def generate(system: str, user: str, *, url: str, model: str, timeout: float) -> str:
    """Send a system + user prompt to Ollama and return the reply text."""
    client = ollama.Client(host=url, timeout=timeout)
    try:
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Temperature 0 keeps answers as repeatable as possible, which evals rely on later
            options={"temperature": 0},
        )
    except (ollama.ResponseError, ConnectionError, httpx.HTTPError) as error:
        raise LLMError(f"LLM request failed: {error}") from error
    return (response.message.content or "").strip()
