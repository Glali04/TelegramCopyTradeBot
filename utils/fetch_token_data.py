import asyncio

from utils.client_sessions_to_servers import http_client
from datetime import datetime
from utils.bsc_utils.swap import swap_tokens
from utils.solana_utils.trade_execution import buy_token
from utils.tracked_tokens import TrackedToken
from config.settings import WSOL_ADDRESS,WBNB_ADDRESS

"""first we will fetch data from dexscreener to get all information about the token, that maybe we will buy. 
depending on how the message was sent in the group, we can get information about the token on various ways, 
the actual contract address or pair id was sent in the channel"""


"""if market cap is between defined limit and token is not on pumpfun or moonshot, we will create an instance of
TrackedToken also we can trade bsc tokens there is the limitation also the market cap, and it must be traded on
pancakeswap"""
async def request_token_information(fetch_token_information: dict, user_name: str):
    # either we will open a client session or we use an already created to this server
    base_url = "https://api.dexscreener.com"
    blockchain = fetch_token_information['blockchain']
    if fetch_token_information["source"] == "DexScreener":
        pair_id = fetch_token_information["pair_id"]
        endpoint = f"latest/dex/pairs/{blockchain}/{pair_id}"
        data = await http_client.fetch(base_url, endpoint)
        token_to_buy = parse_by_pair_id(pair_id, blockchain, data)
    else:
        token_address = fetch_token_information["token_address"]
        endpoint = f"tokens/v1/{blockchain}/{token_address}"
        data = await http_client.fetch(base_url, endpoint)
        token_to_buy = parse_by_token_address(token_address, blockchain, data)
    # we checked the token if token has market cap in given range and is not listed on pump or moonshot, we will go
    # and buy it
    if token_to_buy:
        token_to_buy.user_name = user_name
        if blockchain == "solana":
            token_to_buy.quote_token = WSOL_ADDRESS
            await buy_token(token_to_buy)
        else:
            print(token_to_buy.router_version)
            token_to_buy.quote_token = WBNB_ADDRESS
            await swap_tokens(token_to_buy, sell_transaction=False)


def parse_by_pair_id(pair_id, blockchain, data):
    if not isinstance(data, dict) or len(data) == 0:
        print(f"No data found for the pairId: {pair_id}, occurred: {datetime.now()}")
        return None

    token_info = data.get("pairs")[0]
    market_cap = token_info.get("marketCap")
    dex_id = token_info.get("dexId")
    print("token was found via dex")

    if market_cap and 25_000 < market_cap < 5_000_000:
        print("market cap was right", market_cap)
        if blockchain == "bsc" and dex_id == "pancakeswap":
            token = TrackedToken(token_info.get("baseToken", {}).get("address"))
            token.router_version = token_info.get("labels")[0]
            return token
        if blockchain == "solana" and dex_id not in ["pumpfun", "moonshot"]:
            return TrackedToken(token_info.get("baseToken", {}).get("address"))
    print(f"market cap is too high/low or it is on the wrong dex, pairId: {pair_id}, occurred: {datetime.now()}")
    return None


def parse_by_token_address(token_address, blockchain, data):
    if not isinstance(data, list) or len(data) == 0:
        print(f"No data found for the pairId: {token_address}, occurred: {datetime.now()}")
        return None

    print("token was found via ca")
    token_info = data[0]
    market_cap = token_info.get("marketCap")
    dex_id = token_info.get("dexId")

    if market_cap and 25_000 < market_cap < 5_000_000:
        print("market cap was right", market_cap)
        if blockchain == "bsc" and dex_id == "pancakeswap":
            print("dex was pancakeswap")
            token = TrackedToken(token_info.get("baseToken", {}).get("address"))
            token.router_version = token_info.get("labels")[0]
            return token
        if blockchain == "solana" and dex_id not in ["pumpfun", "moonshot"]:
            return TrackedToken(token_info.get("baseToken", {}).get("address"))
    print(f"market cap is too high/low or it is on the wrong dex, pairId: {token_address}, occurred: {datetime.now()}")
    return None