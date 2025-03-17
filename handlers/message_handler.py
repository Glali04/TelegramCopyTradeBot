from handlers.client import app
from utils import regex, fetch_token_data
import asyncio

#it will fetch messages from caller groups, via TCP socket, if message is sent in group we will get it immediately
@app.on_message()
async def callers_messages(client, message):
    print(message)
    token_to_buy = regex.extract_token_address(message.text)
    print(token_to_buy)
    # if ca/pairid was found, we are going to fetch information about the token
    if token_to_buy is not None:
        fetch_token_data.token_pair_data(token_to_buy)


# ✅ Start background tasks when bot starts
@app.on_startup()
async def start_tasks():
    asyncio.create_task(fetch_token_data.token_pair_data)