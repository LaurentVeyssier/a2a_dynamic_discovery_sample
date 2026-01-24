import httpx
import uuid
import json
import asyncio

async def main():
    pa_url = "http://127.0.0.1:9000/a2a/personal_assistant"
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "message_id": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": "I want to book a flight to Dublin on 2026-05-15. Please handle everything."}]
            },
            "metadata": {}
        },
        "id": 1
    }
    
    print(f"Sending request to Personal Assistant at {pa_url}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(pa_url, json=payload, timeout=120.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Response from PA:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
