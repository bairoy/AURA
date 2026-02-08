#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from src.cartesia_tts import CartesiaTTS

async def test_tts():
    print("Starting Cartesia TTS test...")
    
    tts = CartesiaTTS()
    
    # Start receiving events in background
    receive_task = asyncio.create_task(receive_audio(tts))
    
    # Give receive task a moment to start listening
    await asyncio.sleep(0.5)
    
    # Send test text
    print("Sending test text...")
    await tts.send_text("Hello world. This is a test.")
    
    # Wait for responses
    await asyncio.sleep(3)
    
    # Close
    await tts.close()
    
    # Cancel the receive task
    receive_task.cancel()
    try:
        await receive_task
    except asyncio.CancelledError:
        print("Receive task cancelled")

async def receive_audio(tts):
    audio_count = 0
    try:
        async for event in tts.receive_events():
            audio_count += 1
            print(f"Received audio chunk {audio_count}: {len(event.audio)} bytes")
    except asyncio.CancelledError:
        print(f"Total audio chunks received: {audio_count}")
        raise

if __name__ == "__main__":
    asyncio.run(test_tts())
