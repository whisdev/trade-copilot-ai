"""Chutes provider for chat completion and scoring. Uses Qwen/Qwen3-32B."""

import httpx
from app.config import settings
from app.prompts import get_system_prompt


def _check_api_key():
    key = (settings.chutes_api_key or "").strip()
    if not key:
        raise ValueError(
            "CHUTES_API_KEY is missing. "
            "Get a key at https://chutes.ai and set it in backend/.env"
        )


def _chutes_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.chutes_api_key.strip()}",
        "Content-Type": "application/json",
    }


async def chat_completion(messages: list[dict], social: str, channel_type: str) -> str:
    """Call Chutes chat completion. messages: [{"role": "user"|"assistant"|"system", "content": "..."}]"""
    _check_api_key()
    system = get_system_prompt(social, channel_type)
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": system}] + list(messages)
    else:
        messages = [{"role": "system", "content": system}] + messages[1:]

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{settings.chutes_base_url}/chat/completions",
                headers=_chutes_headers(),
                json={
                    "model": settings.chutes_model,
                    "messages": messages,
                    "max_tokens": settings.chutes_max_tokens,
                    "temperature": settings.chutes_temperature,
                    "stream": False,
                },
                timeout=120.0,
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        print(f"Chutes API error: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        print(f"Chutes request failed: {e}")
        raise
    except Exception as e:
        print(f"Chutes chat_completion error: {e}")
        raise

    choice = data.get("choices", [{}])[0]
    return (choice.get("message") or {}).get("content", "").strip()


ATTRACT_SCORER_PROMPT = """You are an analyst. Given a conversation turn where the first speaker is a professional trader (with trading bot experience) and the second is their reply to a potential collaborator, score how likely that reply is to ATTRACT the other person to want to collaborate (e.g. trust them, want to work together, see them as the right partner).

Score from 0 to 100:
- 0–30: Generic, off-putting, or weak; would not attract.
- 31–60: Okay but not compelling; some value but not memorable.
- 61–80: Strong; demonstrates expertise and credibility; likely to attract serious interest.
- 81–100: Highly compelling; clear authority, value, and "this is the person I want to work with" vibe.

Reply with ONLY a single integer (0–100), nothing else."""


async def score_attractiveness(user_msg: str, assistant_msg: str) -> int:
    """Score 0-100 how attractive the assistant reply is for collaboration."""
    _check_api_key()
    if not assistant_msg:
        return 0
    prompt = f"User/collaborator said:\n{user_msg}\n\nTrader replied:\n{assistant_msg}\n\nScore (0-100):"
    messages = [
        {"role": "system", "content": ATTRACT_SCORER_PROMPT},
        {"role": "user", "content": prompt},
    ]
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.chutes_base_url}/chat/completions",
            headers=_chutes_headers(),
            json={
                "model": settings.chutes_model,
                "messages": messages,
                "max_tokens": 16,
                "temperature": 0.3,
                "stream": False,
            },
            timeout=60.0,
        )
        r.raise_for_status()
        data = r.json()
    content = (data.get("choices", [{}])[0].get("message") or {}).get("content", "0").strip()
    for part in content.replace(",", " ").split():
        if part.isdigit():
            return min(100, max(0, int(part)))
    return 0
