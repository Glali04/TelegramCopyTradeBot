import asyncio
import atexit
from utils.fetch_token_price import track_token_prices_for_bsc, track_token_prices_for_solana
from utils.solana_utils import sol_price
from utils.bsc_utils import bnb_price, gas_price
from handlers.client import client
from handlers.message_handler import process_messages
from utils.client_sessions_to_servers import http_client
from utils.solana_utils.solana_client import set_up_async_client_for_solana_rpc
from database.commands import process_db_queue

async def main():
    print("🚀 Starting userbot...")

    # Set up Solana async client
    await set_up_async_client_for_solana_rpc()

    # This is where your event loop is managed
    loop = asyncio.get_event_loop()

    # Run background tasks using the same loop
    loop.create_task(sol_price.sol_price_loop())
    loop.create_task(bnb_price.bnb_price_loop())
    loop.create_task(gas_price.bsc_gas_price_loop())
    loop.create_task(process_messages())
    loop.create_task(process_db_queue())
    loop.create_task(track_token_prices_for_solana())
    loop.create_task(track_token_prices_for_bsc())

    # Start Telethon client
    async with client:
        print("✅ Connected to Telegram!")
        await client.run_until_disconnected()
    print("✅ Bot started and listening for messages...")

# Clean exit
atexit.register(lambda: asyncio.run(client.disconnect()))
atexit.register(lambda: asyncio.run(http_client.close()))

if __name__ == "__main__":
    # Run the main coroutine using asyncio.run() directly here.
    asyncio.run(main())