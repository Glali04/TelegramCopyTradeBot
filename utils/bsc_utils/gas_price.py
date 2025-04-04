import asyncio
from utils.client_sessions_to_servers import http_client

bsc_gas_price = None


async def update_gas_price():
    global bsc_gas_price
    base_url = "https://api.bscscan.com"
    endpoint = "api?module=gastracker&action=gasoracle&apikey=Y9GMA8TN45MVMCM6UEBZMVNX9KFFSTEFMJ"
    data = await http_client.fetch(base_url, endpoint)
    if data.get("message") == "OK":
        fast_gas_price = float(data.get("result", {}).get("FastGasPrice"))
        if fast_gas_price < 2:
            bsc_gas_price = fast_gas_price * 1.02  # Add 2% (since fast price is already high)
        elif fast_gas_price < 5:
            bsc_gas_price = fast_gas_price * 1.05  # Add 5%
        elif fast_gas_price < 10:
            bsc_gas_price = fast_gas_price * 1.10  # Add 10%
        else:
            bsc_gas_price = fast_gas_price * 1.20  # Add 20% for high congestion


async def bsc_gas_price_loop():
    while True:
        await update_gas_price()
        await asyncio.sleep(5)


async def get_bsc_gas_price():
    global bsc_gas_price
    while bsc_gas_price is None:
        await asyncio.sleep(1)
    return bsc_gas_price
