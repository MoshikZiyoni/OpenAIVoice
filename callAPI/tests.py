from django.test import TestCase

# Create your tests here.
# Save as test_ws.py and run: python test_ws.py
import asyncio
import websockets

async def test():
    uri = "wss://web-production-7204.up.railway.app/media-stream/?batch_id=d596f70f-1a2c-4fd1-8c93-71836f129491"
    async with websockets.connect(uri) as websocket:
        print("Connected!")

asyncio.run(test())