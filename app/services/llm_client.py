import httpx

from app.core.settings import settings


async def chat_complete(system: str, user: str) -> str:
    url = f"{settings.llm_base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "user", "content": f"{system}\n\n{user}"},
        ],
        "temperature": 0.4,
        "max_tokens": 256,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "choices" not in data:
            raise RuntimeError(f"LLM response missing choices: {data}")

    return data["choices"][0]["message"]["content"]