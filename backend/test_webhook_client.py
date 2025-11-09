import asyncio
import httpx

async def send_webhook():
    url = "http://localhost:8000/webhook"
    headers = {
        "Content-Type": "application/json",
        "X-Signature": "test_signature"
    }
    payload = {
        "secret": "test",
        "tv": {
            "exchange": "BINANCE",
            "symbol": "BTCUSDT",
            "action": "buy"
        },
        "execution_intent": {
            "type": "signal",
            "side": "buy"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            print(f"Webhook response status: {response.status_code}")
            print(f"Webhook response body: {response.json()}")
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(send_webhook())
