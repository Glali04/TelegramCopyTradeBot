# for now, it will only work with solana_utils later I will maybe implement every chain

from utils import sol_price, fetch_token_price
from handlers.client import app
from utils.client_sessions_to_servers import http_client
from utils.solana_utils.solana_client import set_up_async_client_for_solana_rpc
import handlers.message_handler  # Import so the decorators register
import asyncio
import atexit


if __name__ == "__main__":
    atexit.register(http_client.close)
    try:
        print("🚀 Starting userbot...")
        # background tasks tracking open trade prices and fetching solana_utils price
        loop = asyncio.get_event_loop()
        loop.run_until_complete(set_up_async_client_for_solana_rpc())
        loop.create_task(sol_price.sol_price_loop())
        loop.create_task(fetch_token_price.track_token_prices())
        app.run()  # Starting the event loop
    finally:
        print("shut down the userbot")
        http_client.close()
