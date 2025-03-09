# for now it will only work with solana later I will maybe implement every chain

from handlers.client import app
import handlers.message_handler # Import so the decorators register

if __name__ == "__main__":
    print("🚀 Starting userbot...")
    app.run()  # This blocks and keeps running