from config.settings import API_ID, API_HASH
from pyrogram import Client

#represent an account connected to the Telegram API, main interface through you interact with Telegrams features
app = Client("channel tracker", api_id=API_ID, api_hash=API_HASH, phone_number="+381621505855")
