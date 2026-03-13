#!/usr/bin/env python3
"""
Test script for OpenAI API - mirrors backend llm.py.
Run from backend/: python test_openai_api.py
"""
import asyncio
import json
import os
from pathlib import Path

# Load .env
from dotenv import load_dotenv
_env = Path(__file__).resolve().parent / ".env"
load_dotenv(_env)

# Parse keys: OPENAI_API_KEYS (comma-separated) or OPENAI_API_KEY
def _get_key_list():
    keys_str = (os.getenv("OPENAI_API_KEYS") or "").strip()
    if keys_str:
        return [k.strip() for k in keys_str.split(",") if k.strip()]
    single = (os.getenv("OPENAI_API_KEY") or "").strip()
    return [single] if single else []


API_KEYS = _get_key_list()
if not API_KEYS:
    print("ERROR: OPENAI_API_KEY or OPENAI_API_KEYS not set in backend/.env")
    print("Use OPENAI_API_KEYS=key1,key2,key3 for multiple keys (tries next on 401/429)")
    exit(1)

BASE_URL = "https://api.openai.com/v1"
RETRYABLE_STATUS = (401, 429)


def _headers(key: str):
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


async def _post_with_rotation(url: str, body: dict, timeout: float):
    """POST, rotating to next key on 401/429."""
    import httpx
    last_err = None
    for i, key in enumerate(API_KEYS):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    url, headers=_headers(key), json=body, timeout=timeout
                )
                if r.status_code in RETRYABLE_STATUS and i < len(API_KEYS) - 1:
                    print(f"   Key #{i + 1} failed ({r.status_code}), trying next...")
                    last_err = httpx.HTTPStatusError(
                        f"HTTP {r.status_code}", request=r.request, response=r
                    )
                    continue
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            last_err = e
            if e.response.status_code in RETRYABLE_STATUS and i < len(API_KEYS) - 1:
                print(f"   Key #{i + 1} failed ({e.response.status_code}), trying next...")
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("No keys succeeded.")


async def test_key_valid():
    """Verify at least one OpenAI API key is valid."""
    data = await _post_with_rotation(
        f"{BASE_URL}/chat/completions",
        {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
        timeout=15.0,
    )
    return data is not None


async def test_non_streaming():
    """Test non-streaming call (matches backend llm.py behavior)."""
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
        "stream": False,
        "max_tokens": 64,
        "temperature": 0.7,
    }
    data = await _post_with_rotation(
        f"{BASE_URL}/chat/completions", body, timeout=30.0
    )
    choice = data.get("choices", [{}])[0]
    content = (choice.get("message") or {}).get("content", "").strip()
    print("[NON-STREAMING] Response:", repr(content))
    return content


async def test_streaming_httpx():
    """Test streaming using httpx. Tries next key on 401/429."""
    import httpx

    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say 'hi' in one word."}],
        "stream": True,
        "max_tokens": 32,
        "temperature": 0.7,
    }

    full_content = []
    last_err = None
    for i, key in enumerate(API_KEYS):
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{BASE_URL}/chat/completions",
                    headers=_headers(key),
                    json=body,
                    timeout=30.0,
                ) as r:
                    if r.status_code in RETRYABLE_STATUS and i < len(API_KEYS) - 1:
                        print(f"   Key #{i + 1} failed ({r.status_code}), trying next...")
                        last_err = httpx.HTTPStatusError(
                            f"HTTP {r.status_code}", request=r.request, response=r
                        )
                        continue
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data)
                                delta = (chunk_json.get("choices", [{}])[0].get("delta") or {}).get("content")
                                if delta:
                                    full_content.append(delta)
                                    print(delta, end="", flush=True)
                            except json.JSONDecodeError:
                                pass
                    break
        except httpx.HTTPStatusError as e:
            last_err = e
            if e.response.status_code in RETRYABLE_STATUS and i < len(API_KEYS) - 1:
                print(f"   Key #{i + 1} failed ({e.response.status_code}), trying next...")
                continue
            raise
    else:
        if last_err:
            raise last_err

    print()
    text = "".join(full_content)
    print(f"[STREAMING] Response: {repr(text)}")
    return text


async def main():
    print("=== OpenAI API Tests ===\n")

    print("0. API key validation...")
    try:
        await test_key_valid()
        print("   OK (key is valid)\n")
    except Exception as e:
        print(f"   FAIL: {e}\n")
        return

    print("1. Non-streaming (backend style)...")
    try:
        await test_non_streaming()
        print("   OK\n")
    except Exception as e:
        print(f"   FAIL: {e}\n")

    print("2. Streaming (httpx)...")
    try:
        await test_streaming_httpx()
        print("   OK\n")
    except Exception as e:
        print(f"   FAIL: {e}\n")

    print("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
