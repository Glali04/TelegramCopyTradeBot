from handlers.client import app
from utils import regex, fetch_token_data
import asyncio


# it will fetch messages from caller groups, via TCP socket, if message is sent in group we will get it immediately
@app.on_message()
async def callers_messages(client, message):
    token_to_buy = regex.extract_token_address(message.text)
    # if ca/pairid was found, we are going to fetch information about the token
    if token_to_buy:
        user_id = message.from_user.id
        asyncio.create_task(fetch_token_data.request_token_information(token_to_buy, user_id))
