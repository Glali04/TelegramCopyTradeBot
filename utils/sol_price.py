import asyncio
from client_sessions_to_servers import http_client

sol_price = None  # Global variable to store latest SOL price
wsol_address = "So11111111111111111111111111111111111111112"


async def fetch_sol_price():
    global sol_price  # Use global variable
    base_url = "https://api.jup.ag"
    endpoint = f"price/v2?ids={wsol_address}"
    data = http_client.fetch(base_url, endpoint)
    sol_price = float(data.get("data", {}).get(f"{wsol_address}", {}).get("price"))


# price fetching loop in the background
async def sol_price_loop():
    while True:
        await fetch_sol_price()
        await asyncio.sleep(1800) # Sleep for 30 minutes

async def get_sol_price():
    while sol_price is None:
        print("Waitting for SOL price update")
        await asyncio.sleep(1)
    return sol_price