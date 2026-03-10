"""OpenRouter provider for chat completion and scoring."""

import httpx
from app.config import settings
from app.prompts import get_system_prompt


def _check_api_key():
    key = (settings.openrouter_api_key or "").strip()
    if not key:
        raise ValueError(
            "OPENROUTER_API_KEY is missing. "
            "Get a key at https://openrouter.ai/keys and set it in backend/.env"
        )


def _openrouter_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/whisdev/traderchat_ai",
    }


async def chat_completion(messages: list[dict], social: str, channel_type: str) -> str:
    """Call OpenRouter chat completion. messages: [{"role": "user"|"assistant"|"system", "content": "..."}]"""
    _check_api_key()
    system = get_system_prompt(social, channel_type)
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": system}] + list(messages)
    else:
        messages = [{"role": "system", "content": system}] + messages[1:]

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=_openrouter_headers(),
                json={
                    "model": settings.openrouter_model,
                    "messages": messages,
                    "max_tokens": settings.openrouter_max_tokens,
                    "temperature": settings.openrouter_temperature,
                    "stream": False,
                },
                timeout=120.0,
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        print(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        print(f"OpenRouter request failed: {e}")
        raise
    except Exception as e:
        print(f"OpenRouter chat_completion error: {e}")
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
            f"{settings.openrouter_base_url}/chat/completions",
            headers=_openrouter_headers(),
            json={
                "model": settings.openrouter_model,
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
