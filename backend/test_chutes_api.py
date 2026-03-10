#!/usr/bin/env python3
"""
Test script for Chutes API - mirrors backend llm.py and user's sample code.
Run from backend/: python test_chutes_api.py
"""
import asyncio
import json
import os
from pathlib import Path

# Load .env
from dotenv import load_dotenv
_env = Path(__file__).resolve().parent / ".env"
load_dotenv(_env)

# Check API key
API_KEY = (os.getenv("CHUTES_API_KEY") or "").strip()
print(API_KEY)
if not API_KEY:
    print("ERROR: CHUTES_API_KEY not set in backend/.env")
    exit(1)

BASE_URL = "https://llm.chutes.ai/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


async def test_non_streaming():
    """Test non-streaming call (matches backend llm.py behavior)."""
    import httpx

    body = {
        "model": "Qwen/Qwen3-14B",
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
        "stream": False,
        "max_tokens": 64,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json=body,
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()

    choice = data.get("choices", [{}])[0]
    content = (choice.get("message") or {}).get("content", "").strip()
    print("[NON-STREAMING] Response:", repr(content))
    return content


async def test_streaming_aiohttp():
    """Test streaming call using aiohttp (user's sample style)."""
    try:
        import aiohttp
    except ImportError:
        print("[STREAMING] aiohttp not installed; skipping. Run: pip install aiohttp")
        return None

    body = {
        "model": "Qwen/Qwen3-32B",
        "messages": [{"role": "user", "content": "Tell me a 250 word story."}],
        "stream": True,
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    full_content = []
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json=body,
        ) as response:
            if response.status != 200:
                text = await response.text()
                print(f"[STREAMING] HTTP {response.status}: {text[:500]}")
                return None

            async for line in response.content:
                line = line.decode("utf-8").strip()
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

    print()
    text = "".join(full_content)
    print(f"[STREAMING] Total chars: {len(text)}")
    return text


async def test_streaming_httpx():
    """Test streaming using httpx (no aiohttp dependency)."""
    import httpx

    body = {
        "model": "Qwen/Qwen3-14B",
        "messages": [{"role": "user", "content": "Say 'hi' in one word."}],
        "stream": True,
        "max_tokens": 32,
        "temperature": 0.7,
    }

    full_content = []
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json=body,
            timeout=30.0,
        ) as r:
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

    print()
    text = "".join(full_content)
    print(f"[STREAMING-HTTPX] Response: {repr(text)}")
    return text


async def main():
    print("=== Chutes API Tests ===\n")

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

    print("3. Streaming (aiohttp, user sample style)...")
    try:
        result = await test_streaming_aiohttp()
        if result is not None:
            print("   OK\n")
    except Exception as e:
        print(f"   FAIL: {e}\n")

    print("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
