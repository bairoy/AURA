#!/usr/bin/env python3
print("Test 1: Python is running")

import asyncio
print("Test 2: asyncio imported")

import websockets
print("Test 3: websockets imported")

import json
print("Test 4: json imported")

import os
from dotenv import load_dotenv
print("Test 5: dotenv imported")

load_dotenv()
api_key = os.getenv("CARTESIA_API_KEY")
print(f"Test 6: API key loaded: {api_key[:20] if api_key else 'NOT SET'}...")

async def main():
    print("Test 7: In async main")
    try:
        print("Test 8: About to connect...")
        uri = f"wss://api.cartesia.ai/tts/websocket?api_key={api_key}&cartesia_version=2025-04-16"
        print(f"Test 9: URI is {uri[:50]}...")
        async with await asyncio.wait_for(websockets.connect(uri), timeout=5) as ws:
            print("Test 10: Connected!")
    except asyncio.TimeoutError:
        print("Test 10: Connection timed out")
    except Exception as e:
        print(f"Test 10: Connection failed: {type(e).__name__}: {e}")

print("Test 11: About to run async main")
try:
    asyncio.run(main())
except Exception as e:
    print(f"Test 11: asyncio.run failed: {e}")

print("Test 12: Done")
