import asyncio
import aiohttp
from client_sessions_to_servers import http_client
from sol_price import sol_price
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from send_transaction import send
# we will separate this module to two parts one for buying given token second to sell given token
#first we need to queue a swap then actually swap the token
#amount we need put it without decimals "raw/integer" format
amount_in_raw = sol_price #TODO
wallet_public_key = None #TODO
base_url = "https://api.jup.ag"

def buy_token(token_to_buy):
    endpoint_for_quote = f"swap/v1/quote?inputMint={token_to_buy['quoteToken']}&outputMint={token_to_buy['baseToken']}&amount={amount_in_raw}" \
               f"slippageBps=1000&restrictIntermediateTokens=true&maxAccounts=64"
    quote = quote_api(endpoint_for_quote)
    endpoint_for_swap = f""
    if quote is not None:
        swap = swap_api(endpoint_for_swap, quote)
        if swap is not None:
            send(swap)

def sell_token(token_to_sell):
    endpoint_for_quote = f"swap/v1/quote?inputMint={token_to_sell['baseToken']}&outputMint={token_to_sell['quoteToken']}&amount={amount_in_raw}" \
               f"slippageBps=1000&restrictIntermediateTokens=true&maxAccounts=64"
    quote = quote_api(endpoint_for_quote)
    endpoint_for_swap = f"swap/v1/swap"
    if quote is not None:
        swap_api(endpoint_for_swap, quote)

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
            swap = await http_client.fetch(base_url, endpoint, swap_endpoint= True, data=body_of_request)
            if isinstance(swap, dict) and len(swap) > 0:
                return swap
            else:
                raise Exception("data is not provided in swap")
    return None

