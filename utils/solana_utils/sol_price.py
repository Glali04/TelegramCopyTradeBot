import asyncio
from utils.client_sessions_to_servers import http_client
from config.settings import WSOL_ADDRESS

sol_price = None  # Global variable to store latest SOL price


async def fetch_sol_price():
    global sol_price  # Use global variable
    base_url = "https://api.jup.ag"
    endpoint = f"price/v2?ids={WSOL_ADDRESS}"
    data = await http_client.fetch(base_url, endpoint)
    sol_price = float(data.get("data", {}).get(f"{WSOL_ADDRESS}", {}).get("price"))
    print("new sol price was set ", sol_price)


# price fetching loop in the background
async def sol_price_loop():
    while True:
        await fetch_sol_price()
        await asyncio.sleep(1800)  # Sleep for 30 minutes


# When another function tries to access sol_price, this function ensures that it waits until sol_price_loop() updates it
# if sol_price has already been fetched, it returns immediately
async def get_sol_price():
    global sol_price  # Explicitly reference the global variable
    while sol_price is None:
        print("Waiting for SOL price update")
        await asyncio.sleep(1)
    return sol_price
