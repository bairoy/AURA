#!/usr/bin/env python3
import asyncio
import json
import os
import websockets
from dotenv import load_dotenv

load_dotenv()

async def test_cartesia_api():
    api_key = os.getenv("CARTESIA_API_KEY")
    
    if not api_key:
        print("ERROR: CARTESIA_API_KEY not set in .env")
        return
    
    print(f"Using API key: {api_key[:20]}...")
    
    url = f"wss://api.cartesia.ai/tts/websocket?api_key={api_key}&cartesia_version=2025-04-16"
    
    try:
        print(f"Connecting to: {url}")
        async with websockets.connect(url) as ws:
            print("Connected!")
            
            # Send request
            payload = {
                "model_id": "sonic-3",
                "text": "Hello world",
                "voice": {
                    "mode": "id",
                    "id": "f6ff7c0c-e396-40a9-a70b-f7607edb6937",
                },
                "output_format": {
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 24000,
                },
                "language": "en",
            }
            
            print(f"Sending: {json.dumps(payload, indent=2)}")
            await ws.send(json.dumps(payload))
            
            # Receive with timeout
            received_count = 0
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    received_count += 1
                    data = json.loads(msg)
                    print(f"Response {received_count}: {json.dumps(data, indent=2)[:500]}")
                    if data.get("done"):
                        print("Received done message, closing")
                        break
            except asyncio.TimeoutError:
                print(f"Timeout after {received_count} messages")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_cartesia_api())
