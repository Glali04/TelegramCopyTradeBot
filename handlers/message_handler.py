from handlers.client import client
from telethon import events
from utils import regex, fetch_token_data
import asyncio
from datetime import datetime

import logging
logging.basicConfig(format='[%(levelname)s %(asctime)s] %(name)s: %(message)s', level=logging.INFO)

# Create an async queue to store messages
message_queue = asyncio.Queue()




# Function to process messages asynchronously
async def process_messages():
    while True:
        message = await message_queue.get()  # Get message from the queue
        print(f"Processing message from: {message.chat_id}, {datetime.now()}")

        # Get text from message or caption (if it's media)
        message_text = message.raw_text if hasattr(message, "raw_text") else None
        if not message_text:
            print("No text found, skipping...")
            message_queue.task_done()
            continue  # Skip this message if it has no text

        # Extract token from the message
        token_to_buy = regex.extract_token_address(message_text)
        try:
            if token_to_buy:
                user_name = await client.get_entity(message.chat_id)  # Fetch chat username
                user_name = user_name.username if user_name.username else "Unknown"
                print(f"Token Found: {token_to_buy} from {user_name}")

                # Asynchronously fetch token information
                loop = asyncio.get_event_loop()
                loop.create_task(fetch_token_data.request_token_information(token_to_buy, user_name))
        finally:
            message_queue.task_done()  # Mark message as processed


# Function to capture messages from Telegram channels
@client.on(events.NewMessage(chats=['CallAnalyserBSC', 'CallAnalyserSol', 'marcellcooks', 'TheCorleoneEmpire',
                                    'gogetacalls', 'dr_crypto_channel']))  # Listens to messages from channels
async def callers_messages(event):
    print(f"Received message from {event.chat_id}, {datetime.now()}, {event.raw_text}")
    await message_queue.put(event.message)  # Add message to queue
