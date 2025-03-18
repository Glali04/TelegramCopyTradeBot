# sending swap transaction to the solana blockchain
# here we will sign and send the sell transaction

import base64
import time
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from solders.transaction import VersionedTransaction
from solders.signature import Signature
from solana.rpc.types import TokenAccountOpts

from utils.tracked_tokens import TrackedToken, tracked_tokens
from utils.solana.solana_client import get_client, get_keypair
from database.commands import insert_query

keypair = get_keypair()


def build_and_sign_transaction(swap_transaction):
    print(swap_transaction)
    transaction = VersionedTransaction.from_bytes(
        base64.decode(swap_transaction))  # first we convert to bytes then deserialize it
    print(transaction)
    signed_tx = VersionedTransaction.populate(transaction.message, [keypair.sign_message(bytes(transaction.message))])
    return signed_tx


async def send_and_confirm_transaction(swap_transaction, token: TrackedToken, out_amount=None, sell_all=False,
                                       sell_transaction=False):
    signed_tx = build_and_sign_transaction(swap_transaction)
    connection = get_client()

    """few times, same time will be more trades for same token, if yes and i buy new token i want to just store the 
    newly bought raw amount not everything when i fetch token account balance that way i will ensure in later sales 
    that do not try to sell more token then what i have"""
    previous_balance = calculate_old_token_balance(token.base_token)

    async for attempt in AsyncRetrying(stop=stop_after_attempt(5), wait=wait_fixed(1.0)):  # Retry up to 5 times
        with attempt:
            try:
                print("🚀 Sending transaction...")
                # node's rpc service receives the transaction, this method immediately succeeds, without waiting for
                # any confirmations.
                signature = await connection.send_raw_transaction(txn=bytes(signed_tx))

                confirmed = await confirm_transaction(connection, signature)

                if confirmed:
                    print(f"✅ Transaction {signature} confirmed!")
                    # we will look at does the transaction is sell or buy transaction
                    if sell_transaction:
                        token.sold += out_amount
                        # transaction is confirmed if we sold everything we will remove it from list else we will take 15% profit taking (strategy)
                        if sell_all:
                            tracked_tokens.remove(token)
                            print("sold all")
                            await insert_query(token.user_id, token.base_token, token.start_time, token.end_time,
                                               token.bought, token.sold, token.exit_reason)
                        else:
                            print("sold 15%")
                            token.raw_amount -= token.raw_amount * 0.15  # 15% profit-taking strategy
                        return True

                    # if we bought given token we will need to add it to tracked tokens
                    token_balance = fetch_token_balance(connection, keypair.pubkey(), token.base_token)

                    if token_balance:
                        balance_for_this_trade = token_balance - previous_balance  # amount we own - owned amount
                        # before this buy transaction
                        token.raw_amount = balance_for_this_trade
                        tracked_tokens.append(token)
                        # more information about why we need this fields in tracked_tokens module
                        timestamp = time.time()
                        token.unix_timestamp = timestamp
                        token.start_time = timestamp
                    return True

                print(f"⚠️ Transaction {signature} failed, retrying...")

            except Exception as e:
                print(f"❌ Error while sending transaction: {str(e)}")

    print("🚨 Max retries reached. Transaction failed.")
    return False  # Failed after all retries


async def confirm_transaction(connection, txid: str):
    async for attempt in AsyncRetrying(stop=stop_after_attempt(15), wait=wait_fixed(0.5)):  # Retry up to 15 times
        with attempt:
            try:
                response = await connection.get_signature_statuses([Signature.from_string(txid)])
                status = response.get("result", {}).get("value")[0]

                if status:
                    confirmation_status = status.get("confirmationStatus")
                    if confirmation_status in ["confirmed", "finalized"]:
                        return True
                    if status.get("err") is not None:
                        print(f"❌ Transaction {txid} failed with error: {status.get('err')}")
                        return False
            except Exception as e:
                print(f"❌ Error while confirming transaction: {str(e)}")

    print(f"⚠️ Timeout reached, assuming transaction {txid} failed.")
    return False


"""one ATA(associated token account) created / wallet, we will get amount from memory instead of fetching from blockchain
it is much faster and more reliable way"""


def calculate_old_token_balance(token_address):
    previous_balance = 0
    for active_trade in tracked_tokens:
        # if mint address is same for both token, means right now we have active trade for this token
        if active_trade.base_token == token_address:
            previous_balance += active_trade.raw_amount
    return previous_balance


async def fetch_token_balance(connection, wallet_pubkey, token_address):
    async for attempt in AsyncRetrying(stop=stop_after_attempt(15), wait=wait_fixed(1.0)):  # Retry up to 5 times
        with attempt:
            try:
                # Get token account by owner
                response = await connection.get_token_accounts_by_owner(
                    owner=wallet_pubkey,
                    opts=TokenAccountOpts(mint=TokenAccountOpts.mint.from_string(token_address))
                )
                token_account_information = response.get("result", {}).get("value")[0]
                if response and token_account_information:
                    # we will store tokens already in raw units(the smallest units of token), that way we reduce
                    # computer units(reduce unnecessary conversions)
                    token_balance = token_account_information.get("account", {}).get("data", {}).get("parsed", {}).get(
                        "info", {}).get("tokenAmount", {}).get("amount")
                    print("raw token balance ", token_balance)
                    return token_balance
                else:
                    print("⚠️ No token account found. Retrying...")

            except Exception as e:
                print(f"❌ Error fetching balance: {e}. Retrying...")

        print("⛔ Failed to fetch balance after retries.")
        return None
