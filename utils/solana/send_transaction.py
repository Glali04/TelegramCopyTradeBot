# sending swap transaction to the solana blockchain
# here we will sign and send the transaction
import solana.rpc.commitment
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from asyncio import sleep
from tracked_tokens import TrackedToken, tracked_tokens
from solders.signature import Signature
import base64

solana_client = None
# we will call this function on beginning of our program
async def set_up_async_client_for_solana_rpc():
    global solana_client
    solana_client = AsyncClient(
        endpoint="https://mainnet.helius-rpc.com/?api-key=ed85df35-708a-40c3-9b03-a6a08fac66ac",
        commitment=solana.rpc.commitment.Confirmed,
        timeout=1
    )


# if the connection is not set with solana node yet we will wait while it is set up
async def get_client():
    while solana_client is None:
        sleep(0.5)
    return solana_client

def build_and_sign_transaction(swap_transaction):
    transaction = VersionedTransaction.from_bytes(base64.decode(swap_transaction)) # first we convert to bytes then deserialize it
    print(transaction)
    signed_tx = VersionedTransaction.populate(transaction.message, [wallet.sign_message(bytes(transaction.message))])
    return signed_tx
async def send_sell_transaction(swap_transaction, token: TrackedToken, sell_all: bool):
    signed_tx = build_and_sign_transaction(swap_transaction)
    connection = get_client()
    #node's rpc service receives the transaction, this method immediately succeeds, without waiting for any confirmations.
    signature = await connection.send_raw_transaction(txn= bytes(signed_tx))
    # we will look at the response if we have result field it means it was able to submit the transaction
    txid = signature.get("result")
    #if it was not submitted successful it will do not have result field txid will be None
    #if not we will try more times, because it is a sell transaction
    

async def check
async def se
"""with open("C:/Users/Lali/trader_bot_wallet", "rb") as wallet:
    byte_keypair = wallet.read()
    keypair = Keypair.from_bytes(byte_keypair)
    print(keypair.pubkey())
    print(keypair.secret())"""
