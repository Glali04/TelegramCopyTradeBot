from config.settings import API_ID, API_HASH
from telethon import TelegramClient

#represent an account connected to the Telegram API, main interface through you interact with Telegrams features
client = TelegramClient("channel_tracker", API_ID, API_HASH)
