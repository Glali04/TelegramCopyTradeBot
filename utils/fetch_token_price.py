# here we will track prices for open_trades once trade is finished we will log it to database for future analyses
import time

from utils.tracked_tokens import tracked_tokens
from asyncio import sleep
from utils.client_sessions_to_servers import http_client
from utils.trade_execution import sell_token

base_url = "https://public-api.birdeye.so"
headers = {
    "accept": "application/json",
    "x-chain": "solana",
    "X-API-KEY": "7f7741539b5f480680daecaf6fe7d1f1"
}


async def track_token_prices():
    while True:
        # first we look do we have active trade
        if len(tracked_tokens) > 0:
            response = await fetch_prices_single_token()
            if response.get("success"):
                await check_prices_single_token(response.get("data", {}).get("value"))
        await sleep(1)


async def fetch_prices_single_token():
    # every time we fetch active trades we will reset list and endpoint
    endpoint = "defi/price?address="
    list_of_active_trade_addresses = []
    for token in tracked_tokens:
        token_address = token.base_token
        endpoint += f"{token_address}"
        response = await http_client.fetch(base_url, endpoint, headers=headers)
    return response

async def check_prices_single_token(value):
    for token in tracked_tokens:
        timestamp = time.time()
        # this means we reached 15% profit first time
        if token.ath_price is None and value >= token.buy_price * 1.15:
            # we set ath to current price and sell 15%
            token.ath_price = value
            token.unix_timestamp = timestamp
            print("reached 15% profit, selling 25%", token.base_token)
            await sell_token(token, sell_all=False)
        # if current price is higher than saved ath we save new ath
        elif token.ath_price and value > token.ath_price:
            token.ath_price = value
            token.unix_timestamp = timestamp
            print("new ath for the token ", token.base_token)
        # if token fall 15% from ath we sell everything:
        elif token.ath_price and value <= token.ath_price * 0.85:
            token.end_time = timestamp
            token.exit_reason = "we reached ath then price dropped 15%, most likely sold in profit"
            print("token price dropped 15% selling all", token.base_token)
            await sell_token(token, sell_all=True)
        # if token dropped 10% from buy price we will sell everything (this will only trigger if we did not reach ath first)
        elif value <= token.buy_price * 0.85:
            token.end_time = timestamp
            token.exit_reason = "we sold in loss"
            print("sold in loss", token.base_token)
            await sell_token(token, sell_all=True)
        # unix_timestamp are time in seconds since epoch 1200 seconds is 20 minutes
        elif token.unix_timestamp + 1200 <= timestamp:
            # it means that price did not reach new ath for 20 minutes and did not price dropped more then 15% so we sell
            # it because it means the token is "inactive" and only uses our cu for and gives latency for our program
            token.end_time = timestamp
            token.exit_reason = "the price did not changed for to long"
            print("token was to long inactive selling all", token.base_token)
            await sell_token(token, sell_all=True)
async def fetch_prices():
    # every time we fetch active trades we will reset list and endpoint
    endpoint = "defi/multi_price?list_address="
    list_of_active_trade_addresses = []
    for token in tracked_tokens:
        token_address = token.base_token
        if token_address not in list_of_active_trade_addresses:
            list_of_active_trade_addresses.append(token_address)
            endpoint += f"{token_address},"
    """removes the last character(the last char will be coma this is the easiest way to remove it), other ways we
    can not surely know when we added the last token to endpoint"""
    endpoint = endpoint[:-1]
    print(f"fetching prices for: {list_of_active_trade_addresses} with endpoint: {endpoint}")
    response = await http_client.fetch(base_url, endpoint, headers=headers)
    return response


async def check_prices(response):
    for token in tracked_tokens:
        token_price = response.get("data", {}).get(f"{token.base_token}", {}).get("value")
        timestamp = time.time()
        # this means we reached 15% profit first time
        if token.ath_price is None and token_price >= token.buy_price * 1.15:
            # we set ath to current price and sell 25%
            token.ath_price = token_price
            token.unix_timestamp = timestamp
            print("reached 15% profit, selling 25%", token.base_token)
            await sell_token(token, sell_all=False)
        # if current price is higher than saved ath we save new ath
        elif token.ath_price and token_price > token.ath_price:
            token.ath_price = token_price
            token.unix_timestamp = timestamp
            print("new ath for the token ", token.base_token)
        # if token fall 15% from ath we sell everything:
        elif token.ath_price and token_price <= token.ath_price * 0.85:
            token.end_time = timestamp
            token.exit_reason = "we reached ath then price dropped 15%, most likely sold in profit"
            print("token price dropped 15% selling all", token.base_token)
            await sell_token(token, sell_all=True)
        # if token dropped 10% from buy price we will sell everything (this will only trigger if we did not reach ath
        # first)
        elif token_price <= token.buy_price * 0.85:
            token.end_time = timestamp
            token.exit_reason = "we sold in loss"
            print("sold in loss", token.base_token)
            await sell_token(token, sell_all=True)
        # unix_timestamp are time in seconds since epoch 1200 seconds is 20 minutes
        elif token.unix_timestamp + 1200 <= timestamp:
            # it means that price did not reach new ath for 20 minutes and did not price dropped more than 15%, so we
            # sell it because it means the token is "inactive" and only uses our cu for and gives latency for our
            # program
            token.end_time = timestamp
            token.exit_reason = "the price did not changed for to long"
            print("token was to long inactive selling all", token.base_token)
            await sell_token(token, sell_all=True)
