import json
import base58

from asyncio import sleep
from solana.rpc.async_api import AsyncClient
import solana.rpc.commitment
from solders.keypair import Keypair

solana_client = None

# we will call this function on beginning of our program
async def set_up_async_client_for_solana_rpc():
    global solana_client
    solana_client = AsyncClient(
        endpoint="https://mainnet.helius-rpc.com/?api-key=ed85df35-708a-40c3-9b03-a6a08fac66ac",
        commitment=solana.rpc.commitment.Confirmed,
        timeout=1
    )


# if the connection is not set with solana node, yet we will wait while it is set up
async def get_client():
    global solana_client
    while solana_client is None:
        sleep(0.5)
    return solana_client


def get_keypair():
    with open("C:/Users/Lali/trader_bot_wallet.json", "r") as wallet:
        data = json.load(wallet)

    print("wallet loaded successfully")
    keypair_bytes = base58.b58decode(data.get("keypair"))
    keypair = Keypair.from_bytes(keypair_bytes)
    return keypair

