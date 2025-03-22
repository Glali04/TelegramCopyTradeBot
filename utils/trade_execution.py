import asyncio
import json
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from utils.client_sessions_to_servers import http_client
from utils.sol_price import get_sol_price
from utils.solana_utils.send_transaction import send_and_confirm_transaction, keypair
from utils.tracked_tokens import TrackedToken
from config.settings import BUY_AMOUNT_IN_US_DOLLAR
# we will separate this module to two parts one for buying given token second to sell given token

# first we need to queue a swap then get swap transaction via jupiter api after that we need to send it to blockchain

# amount we need put in without decimals "raw/integer" format

buy_in = float(BUY_AMOUNT_IN_US_DOLLAR)  # we want to buy every token with this amount of $

wallet_public_key = keypair.pubkey()
base_url = "https://api.jup.ag"
print(wallet_public_key)


async def buy_token(token_to_buy: TrackedToken):
    sol_price = await get_sol_price()  # we will get sol price in $
    raw_amount_sol = get_raw_amount_of_sol(sol_price)
    endpoint_for_quote = f"swap/v1/quote?inputMint={token_to_buy.quote_token}&outputMint={token_to_buy.base_token}" \
                         f"&amount={raw_amount_sol}" \
                         f"&slippageBps=1000&restrictIntermediateTokens=true&maxAccounts=64"
    quote = await quote_api(endpoint_for_quote)
    if quote:
        endpoint_for_swap = f"swap/v1/swap"
        swap = await swap_api(endpoint_for_swap, quote)
        if swap:
            token_to_buy.bought = raw_amount_sol
            result = await send_and_confirm_transaction(swap.get("swapTransaction"),
                                                        token_to_buy)
            # Send only the Transaction, which we will send to blockchain
            if result:
                print(f"successfully bought the token: {token_to_buy.base_token}")
            else:
                print(f"error occurred while buying the token: {token_to_buy.base_token}")


async def sell_token(token_to_sell: TrackedToken, sell_all: bool):
    if sell_all:
        sell_amount = token_to_sell.raw_amount
    else:
        sell_amount = token_to_sell.raw_amount * 0.25

    endpoint_for_quote = f"swap/v1/quote?inputMint={token_to_sell.base_token}&outputMint={token_to_sell.quote_token}" \
                         f"&amount={int(sell_amount)}" \
                         f"&slippageBps=1000&restrictIntermediateTokens=true&maxAccounts=64"
    quote = await quote_api(endpoint_for_quote)
    if quote:
        endpoint_for_swap = f"swap/v1/swap"
        out_amount = int(quote.get("outAmount"))
        swap = await swap_api(endpoint_for_swap, quote)
        if swap:
            result = await send_and_confirm_transaction(swap.get("swapTransaction"), token_to_sell,
                                                        out_amount=out_amount, sell_all=sell_all, sell_transaction=True)
            if result:
                print(f"successfully sold the token: {token_to_sell.base_token}")
            else:
                print(f"error occurred while selling the token: {token_to_sell.base_token}")


async def quote_api(endpoint):
    async for attempt in AsyncRetrying(stop=stop_after_attempt(2), wait=wait_fixed(1.0)):
        with attempt:
            quote = await http_client.fetch(base_url, endpoint)
            if isinstance(quote, dict) and len(quote) > 0:
                return quote
            else:
                raise Exception("data is not provided in quote")
    return None


async def swap_api(endpoint, quote):
    data = json.dumps({
        "userPublicKey": str(wallet_public_key),
        "prioritizationFeeLamports": {
            "priorityLevelWithMaxLamports": {
                "maxLamports": 1000000,
                "global": False,
                "priorityLevel": "veryHigh"
            }
        },
        "dynamicComputeUnitLimit": True,
        "quoteResponse": quote
    })
    async for attempt in AsyncRetrying(stop=stop_after_attempt(2), wait=wait_fixed(1.0)):
        with attempt:
            print(data)
            swap = await http_client.fetch(base_url, endpoint, swap_endpoint=True, data=data)
            if isinstance(swap, dict) and len(swap) > 0:
                return swap
            else:
                raise Exception("data is not provided in swap")
    return None


def get_raw_amount_of_sol(sol_price):
    amount_in_sol = buy_in / sol_price  # (e.x 0.8 = 100 / 124)
    # now we need to convert it to integers (because on the blockchain, token amounts are stored as integers(not
    # decimals), solana_utils has 9 decimals)
    raw_amount = int(amount_in_sol * 10 ** 9)  # 9 is decimals what wsol support
    return raw_amount