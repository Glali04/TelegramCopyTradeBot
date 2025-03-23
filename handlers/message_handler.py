from handlers.client import app
from pyrogram import filters
from utils import regex, fetch_token_data
import asyncio

# Create an async queue to store messages
message_queue = asyncio.Queue()

# Function to process messages asynchronously
async def process_messages():
    while True:
        message = await message_queue.get()  # Get message from the queue
        print(f"Processing message from: {message.sender_chat.username}")

        # Get text from message or caption (if it's media)
        message_text = message.text if message.text else message.caption
        if not message_text:
            print("No text found, skipping...")
            message_queue.task_done()
            continue  # Skip this message if it has no text

        # Extract token from the message
        token_to_buy = regex.extract_token_address(message_text)
        if token_to_buy:
            user_id = message.sender_chat.username
            print(f"Token Found: {token_to_buy} from {user_id}")

            # Asynchronously fetch token information
            asyncio.create_task(fetch_token_data.request_token_information(token_to_buy, user_id))

        message_queue.task_done()  # Mark message as processed


# Function to capture messages from Telegram channels
@app.on_message(filters.channel)  # Listens to messages from channels
async def callers_messages(client, message):
    print(f"Received message from {message.sender_chat.username}")
    await message_queue.put(message)  # Add message to queue
