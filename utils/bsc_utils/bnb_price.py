import asyncio
from utils.client_sessions_to_servers import http_client
from config.settings import WBNB_ADDRESS, headers_for_bsc

bnb_price = None  # Global variable to store latest BNB price


async def fetch_bnb_price():
    global bnb_price  # Use global variable
    base_url = "https://public-api.birdeye.so"
    endpoint = f"defi/price?address={WBNB_ADDRESS}"
    data = await http_client.fetch(base_url, endpoint, headers=headers_for_bsc)
    bnb_price = float(data.get("data", {}).get("value"))
    print("new bnb price was set ", bnb_price)


# price fetching loop in the background
async def bnb_price_loop():
    while True:
        await fetch_bnb_price()
        await asyncio.sleep(1800)  # Sleep for 30 minutes


# When another function tries to access bnb_price, this function ensures that it waits until bnb_price_loop() updates it
# if bnb_price has already been fetched, it returns immediately
async def get_bnb_price():
    global bnb_price  # Explicitly reference the global variable
    while bnb_price is None:
        print("Waiting for BNB price update")
        await asyncio.sleep(1)
    return bnb_price