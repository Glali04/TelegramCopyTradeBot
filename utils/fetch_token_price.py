# here we will track prices for open_trades once trade is finished we will log it to database for future analyses
import time

from utils.tracked_tokens import solana_tracked_tokens, bsc_tracked_tokens
from asyncio import sleep
from utils.client_sessions_to_servers import http_client
from utils.solana_utils.trade_execution import sell_token
from utils.bsc_utils.swap import swap_tokens
from config.settings import headers_for_solana, headers_for_bsc


base_url = "https://public-api.birdeye.so"


async def track_token_prices_for_solana():
    while True:
        # first we look do we have active trade
        if len(solana_tracked_tokens) > 0:
            response = await fetch_prices(solana_tracked_tokens, headers_for_solana)
            if response.get("success"):
                await check_prices(response, solana_tracked_tokens, "solana")
        await sleep(1)


async def track_token_prices_for_bsc():
    while True:
        # first we look do we have active trade
        if len(bsc_tracked_tokens) > 0:
            response = await fetch_prices(bsc_tracked_tokens, headers_for_bsc)
            if response.get("success"):
                await check_prices(response, bsc_tracked_tokens, "bsc")
        await sleep(1)


async def fetch_prices(tracked_tokens, headers):
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


async def check_prices(response, tracked_tokens, blockchain):
    if blockchain == "solana":
        sell = sell_token # ✅ Assign function reference
    else:
        sell = swap_tokens
    for token in tracked_tokens:
        token_price = response.get("data", {}).get(f"{token.base_token}", {}).get("value")
        """i added also to check do we have token_price because if we bought token while we checking the previous token
        price fetch for active trades, for this token we will not have price(because the token is added to token list
        but price is not fetched for it) and the program will throw error, for other statements we already know do we
        have price because we check ath first"""
        if token_price is None:
            continue
        timestamp = time.time()
        loss_precentage = 0.8 if token.reached_30_precentage_profit else 0.9
        # this means we reached 15% profit first time
        if (token.ath_price is None) and (token_price >= token.buy_price * 1.15):
            # we set ath to current price and sell 30%
            token.ath_price = token_price
            token.unix_timestamp = timestamp
            print("reached 15% profit, selling 30%", token.base_token)
            await sell(token, sell_all=False) # Partial sell
        # if current price is higher than saved ath we save new ath
        elif token_price >= token.buy_price * 1.30:
            token.ath_price = token_price
            token.unix_timestamp = timestamp
            print("reached 30% profit, selling another 30%", token.base_token)
            await sell(token, sell_all=False)  # Partial sell
        elif token.ath_price and token_price > token.ath_price:
            token.ath_price = token_price
            token.unix_timestamp = timestamp
            print("new ath for the token ", token.base_token)
        # if token fall 10% or 20% from ath we sell everything:
        elif token.ath_price and token_price <= token.ath_price * loss_precentage:
            token.end_time = timestamp
            token.exit_reason = "we reached ath then price dropped 10% or 20%, most likely sold in profit"
            print("token price dropped 10% or 30% selling all", token.base_token, loss_precentage)
            await sell(token, sell_all=True)
        # if token dropped 10% from buy price we will sell everything (this will only trigger if we did not reach ath
        # first)
        elif token_price <= token.buy_price * 0.9:
            token.end_time = timestamp
            token.exit_reason = "we sold in loss"
            print("sold in loss", token.base_token)
            await sell(token, sell_all=True)
        # unix_timestamp are time in seconds since epoch 1200 seconds is 20 minutes
        elif token.unix_timestamp + 1200 <= timestamp:
            # it means that price did not reach new ath for 20 minutes and did not price dropped more than 15%, so we
            # sell it because it means the token is "inactive" and only uses our cu for and gives latency for our
            # program
            token.end_time = timestamp
            token.exit_reason = "the price did not changed for to long"
            print("token was to long inactive selling all", token.base_token)
            await sell(token, sell_all=True)
        print(f"{token.base_token}, {token.buy_price}, {token_price}")
