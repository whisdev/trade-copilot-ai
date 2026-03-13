"""OpenAI provider for chat completion and scoring."""

import httpx
from app.config import settings
from app.prompts import get_system_prompt

# 401=invalid key, 429=rate limit - try next key
_RETRYABLE_STATUS = (401, 429)


def _check_api_keys():
    keys = settings.get_openai_key_list()
    if not keys:
        raise ValueError(
            "OPENAI_API_KEY or OPENAI_API_KEYS is missing. "
            "Get keys at https://platform.openai.com/api-keys and set in backend/.env"
        )


def _headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


async def _post_with_key_rotation(
    url: str, json_body: dict, timeout: float
) -> dict:
    """POST to OpenAI API, rotating to next key on 401/429."""
    keys = settings.get_openai_key_list()
    if not keys:
        raise ValueError("No OpenAI API keys configured.")
    last_err = None
    for i, key in enumerate(keys):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    url,
                    headers=_headers(key),
                    json=json_body,
                    timeout=timeout,
                )
                if r.status_code in _RETRYABLE_STATUS and i < len(keys) - 1:
                    print(f"OpenAI key #{i + 1} failed ({r.status_code}), trying next...")
                    last_err = httpx.HTTPStatusError(
                        f"HTTP {r.status_code}", request=r.request, response=r
                    )
                    continue
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            last_err = e
            if e.response.status_code in _RETRYABLE_STATUS and i < len(keys) - 1:
                print(f"OpenAI key #{i + 1} failed ({e.response.status_code}), trying next...")
                continue
            raise
        except httpx.RequestError as e:
            print(f"OpenAI request failed: {e}")
            raise
    if last_err:
        raise last_err
    raise RuntimeError("No keys succeeded.")


async def chat_completion(messages: list[dict], social: str, channel_type: str) -> str:
    """Call OpenAI chat completion. messages: [{"role": "user"|"assistant"|"system", "content": "..."}]"""
    _check_api_keys()
    system = get_system_prompt(social, channel_type)
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": system}] + list(messages)
    else:
        messages = [{"role": "system", "content": system}] + messages[1:]

    try:
        data = await _post_with_key_rotation(
            f"{settings.openai_base_url}/chat/completions",
            {
                "model": settings.openai_model,
                "messages": messages,
                "max_tokens": settings.openai_max_tokens,
                "temperature": settings.openai_temperature,
                "stream": False,
            },
            timeout=120.0,
        )
    except httpx.HTTPStatusError as e:
        print(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        print(f"OpenAI request failed: {e}")
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
    _check_api_keys()
    if not assistant_msg:
        return 0
    prompt = f"User/collaborator said:\n{user_msg}\n\nTrader replied:\n{assistant_msg}\n\nScore (0-100):"
    messages = [
        {"role": "system", "content": ATTRACT_SCORER_PROMPT},
        {"role": "user", "content": prompt},
    ]
    data = await _post_with_key_rotation(
        f"{settings.openai_base_url}/chat/completions",
        {
            "model": settings.openai_model,
            "messages": messages,
            "max_tokens": 16,
            "temperature": 0.3,
            "stream": False,
        },
        timeout=60.0,
    )
    content = (data.get("choices", [{}])[0].get("message") or {}).get("content", "0").strip()
    for part in content.replace(",", " ").split():
        if part.isdigit():
            return min(100, max(0, int(part)))
    return 0
