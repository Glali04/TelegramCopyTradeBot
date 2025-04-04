# sending swap transaction to the solana_utils blockchain
# here we will sign and send the sell transaction
import asyncio
import base64
import time
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from solders.transaction import VersionedTransaction
from solders.message import to_bytes_versioned
from solders.signature import Signature
from solders.pubkey import Pubkey
from solders.transaction_status import TransactionStatus, TransactionConfirmationStatus
from solana.rpc.types import TokenAccountOpts

from utils.tracked_tokens import TrackedToken, solana_tracked_tokens
from utils.solana_utils.solana_client import get_client, get_keypair
from database.commands import save_trade
from config.settings import BUY_AMOUNT_IN_US_DOLLAR

keypair = get_keypair()


def build_and_sign_transaction(swap_transaction):
    # first we convert base64-encoded string to bytes then deserialize it
    transaction = VersionedTransaction.from_bytes(base64.b64decode(swap_transaction))
    signed_tx = VersionedTransaction.populate(transaction.message, [keypair.sign_message(
        to_bytes_versioned(transaction.message))])
    return signed_tx


async def send_and_confirm_transaction(swap_transaction, token: TrackedToken, sell_transaction=False,
                                       sell_all=False, out_amount=None):
    signed_tx = build_and_sign_transaction(swap_transaction)
    connection = await get_client()

    """few times, same time will be more trades for same token, if yes and i buy new token i want to just store the 
    newly bought raw amount not everything when i fetch token account balance that way i will ensure in later sales 
    that do not try to sell more token then what i have"""

    attempt_counter = 0
    async for attempt in AsyncRetrying(stop=stop_after_attempt(1), wait=wait_fixed(1)):  # Retry up to 2 times
        with attempt:
            try:
                attempt_counter += 1
                print("Sending transaction...")
                # node's rpc service receives the transaction, this method immediately succeeds, without waiting for
                # any confirmations.
                # Send the transaction it will return SendTransactionResp object
                response = await connection.send_raw_transaction(txn=bytes(signed_tx))
                signature = response.value  # Extracts the signature from SendTransactionResp

                confirmed = await confirm_transaction(connection, signature)

                if confirmed:
                    print(f"✅ Transaction {signature} confirmed!")
                    # we will look at does the transaction is sell or buy transaction
                    if sell_transaction:
                        token.sold += out_amount
                        print(token.sold)
                        print(token.user_name)
                        # transaction is confirmed if we sold everything we will remove it from list else we will
                        # take 15% profit taking (strategy)
                        if sell_all:
                            solana_tracked_tokens.remove(token)
                            print("sold all")
                            await save_trade(token.user_name, token.base_token, token.start_time, token.end_time,
                                             token.bought, token.sold, token.exit_reason)
                        else:
                            print("sold 25%")
                            token.raw_amount -= int(token.raw_amount * 0.25)  # 25% profit-taking strategy
                        print("token sold")
                        return True

                    # from confirmed transaction we will get the amount of token we bought
                    token_balance = await fetch_balance_for_trade_from_transaction(connection, signature,
                                                                                   token, keypair.pubkey())
                    print("token bought successfully")
                    if token_balance:
                        # the raw balance of token we bought with this trade
                        token.raw_amount = token_balance
                        # if we bought given token we will need to add it to tracked tokens
                        solana_tracked_tokens.append(token)
                        # more information about why we need this fields in tracked_tokens module
                        timestamp = time.time()
                        # with this we track does the token still actively traded
                        token.unix_timestamp = timestamp
                        # goes in database
                        token.start_time = timestamp
                    return True

                # 🚨 If the transaction is not confirmed, raise an error so Tenacity retries
                raise Exception(f"⚠️ Transaction {signature} failed, retrying...")

            except Exception as e:
                print(f"❌ Error while sending transaction (attempt {attempt_counter}): {str(e)}")
                # 🚨 Ensure the exception is raised so Tenacity retries

    print(f"🚨 Max retries reached. Transaction failed.{attempt_counter} attempts")
    return False  # Failed after all retries


async def confirm_transaction(connection, txid):
    attempt_counter = 0
    async for attempt in AsyncRetrying(stop=stop_after_attempt(20), wait=wait_fixed(1)):  # Retry up to 20 times
        with attempt:
            try:
                attempt_counter += 1

                response = await connection.get_signature_statuses([txid])
                status = response.value[0]

                if status is None:
                    raise Exception("from the response we get None, we will try again")
                if status.confirmation_status == TransactionConfirmationStatus.Confirmed or TransactionConfirmationStatus.Finalized:
                    return True
                if status.err is not None:
                    print(f"❌ Transaction {txid} failed with error: {status.get('err')}")
                    return False
                raise Exception("something went wrong we will try again")

            except Exception as e:
                print(f"❌ Error while confirming transaction: {str(e)} at {time.time()} {attempt_counter} attempt")
                raise  # 🚨 Ensure the exception is raised so Tenacity retries

    # 🚨 If we reach here, transaction was NOT confirmed after all retries → Raise error
    print(f"❌ Timeout reached, assuming transaction {txid} failed after {attempt_counter} attempts.")
    return False


async def fetch_balance_for_trade_from_transaction(connection, txid, token, wallet_pubkey):
    attempt_counter = 0
    async for attempt in AsyncRetrying(stop=stop_after_attempt(5), wait=wait_fixed(1)):  # Retry up to 5 times
        with attempt:
            try:
                attempt_counter += 1
                # Fetch transaction details
                response = await connection.get_transaction(
                    txid, encoding="jsonParsed", max_supported_transaction_version=0
                )

                if not response:
                    raise Exception("❌ No response from RPC")

                tx_data = response.value.transaction
                if not tx_data:
                    raise Exception("❌ Transaction data is empty")

                # Extract pre and post token balances safely
                pre_balances = tx_data.meta.pre_token_balances
                post_balances = tx_data.meta.post_token_balances

                pre_balance = 0
                post_balance = 0
                decimals = 0
                # Extract the balance for the given token mint and wallet
                for entry in pre_balances:
                    if str(entry.mint) == token.base_token and entry.owner == wallet_pubkey:
                        pre_balance = int(entry.ui_token_amount.amount)  # Raw units
                        print(f"Pre-balance: {pre_balance}")

                for entry in post_balances:
                    if str(entry.mint) == token.base_token and entry.owner == wallet_pubkey:
                        post_balance = int(entry.ui_token_amount.amount)
                        decimals = int(entry.ui_token_amount.decimals)
                        print(f"Post-balance: {post_balance}, decimals: {decimals}")

                token_received = post_balance - pre_balance
                bought_with = float(BUY_AMOUNT_IN_US_DOLLAR)
                token.buy_price = float(bought_with / (token_received / (10 ** decimals)))
                print(f"Token balance change: {token_received} raw units")
                print(f"buy price {token.buy_price}")

                return token_received


            except Exception as e:
                print(f"❌ Error fetching balance from txid {txid}: {e}. {attempt_counter} attempt Retrying...")
                raise

    print("⛔ Failed to fetch balance after retries.")
    return None
