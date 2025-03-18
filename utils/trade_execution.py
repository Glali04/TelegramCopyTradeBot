from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
import aiohttp

from utils.client_sessions_to_servers import http_client
from utils.sol_price import get_sol_price
from utils.solana.send_transaction import send_and_confirm_transaction, keypair
from utils.tracked_tokens import TrackedToken

# we will separate this module to two parts one for buying given token second to sell given token

# first we need to queue a swap then get swap transaction via jupiter api after that we need to send it to blockchain

# amount we need put in without decimals "raw/integer" format

buy_in = 1.00  # we want to buy every token with this amount of $

wallet_public_key = keypair.pubkey()
base_url = "https://api.jup.ag"
print(wallet_public_key)


async def buy_token(token_to_buy: TrackedToken):
    sol_price = await get_sol_price()  # we will get sol price in $
    print("sol price", sol_price)
    raw_amount_sol = get_raw_amount_of_sol(sol_price)
    print("raw amount of sol", raw_amount_sol)
    print(token_to_buy.quote_token)
    endpoint_for_quote = f"swap/v1/quote?inputMint={token_to_buy.quote_token}&outputMint={token_to_buy.base_token}" \
                         f"&amount={raw_amount_sol}" \
                         f"slippageBps=1000&restrictIntermediateTokens=true&maxAccounts=64"
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
                print(f"error occurred while selling the token: {token_to_buy.base_token}")


async def sell_token(token_to_sell: TrackedToken, sell_all: bool):
    if sell_all:
        sell_amount = token_to_sell.raw_amount
    else:
        sell_amount = token_to_sell.raw_amount * 0.15

    endpoint_for_quote = f"swap/v1/quote?inputMint={token_to_sell.base_token}&outputMint={token_to_sell.quote_token}" \
                         f"&amount={sell_amount}" \
                         f"slippageBps=1000&restrictIntermediateTokens=true&maxAccounts=64"
    quote = await quote_api(endpoint_for_quote)
    if quote:
        endpoint_for_swap = f"swap/v1/swap"
        out_amount = int(quote.get("outAmount"))
        swap = await swap_api(endpoint_for_swap, quote)
        if swap:
            result = await send_and_confirm_transaction(swap.get("swapTransaction"), out_amount, token_to_sell,
                                                        sell_all, sell_transaction=True)
            if result:
                print(f"successfully sold the token: {token_to_sell.base_token}")
            else:
                print(f"error occurred while selling the token: {token_to_sell.base_token}")


async def quote_api(endpoint):
    async for attempt in AsyncRetrying(stop=stop_after_attempt(2), wait=wait_fixed(1.0)):
        with attempt:
            quote = await http_client.fetch(base_url, endpoint)
            if isinstance(quote, dict) and len(quote) > 0:
                print("successfully get quote")
                return quote
            else:
                raise Exception("data is not provided in quote")
    return None


async def swap_api(endpoint, quote):
    data = {
        "userPublicKey": {wallet_public_key},
        "prioritizationFeeLamports": {
            "priorityLevelWithMaxLamports": {
                "global": False,
                "priorityLevel": "veryHigh"
            }
        },
        "dynamicComputeUnitLimit": True,
        "quoteResponse": {quote}
    }
    body_of_request = aiohttp.FormData(data)
    async for attempt in AsyncRetrying(stop=stop_after_attempt(2), wait=wait_fixed(1.0)):
        with attempt:
            swap = await http_client.fetch(base_url, endpoint, swap_endpoint=True, data=body_of_request)
            if isinstance(swap, dict) and len(swap) > 0:
                print("successfully get swap")
                return swap
            else:
                raise Exception("data is not provided in swap")
    return None


def get_raw_amount_of_sol(sol_price):
    amount_in_sol = buy_in / sol_price  # (e.x 0.8 = 100 / 124)
    # now we need to convert it to integers (because on the blockchain, token amounts are stored as integers(not
    # decimals), solana has 9 decimals)
    raw_amount = int(amount_in_sol * 10 ** 9)  # 9 is decimals what wsol support
    return raw_amount
