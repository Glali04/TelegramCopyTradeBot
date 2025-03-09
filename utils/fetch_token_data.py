from utils.client_sessions_to_servers import http_client
from datetime import datetime
from utils.trade_execution import buy_token


# first we will fetch data from dexscreener to get all information about the token we will maybe buy.
# depending on how the message was sent in the group, we can get various information about the token, the actual ca or pair id
async def request_token_information(token_to_buy):
    # either we will open a client session or we use an already created to this server
    base_url = "https://api.dexscreener.com"
    endpoint = None
    token_to_buy = None
    if token_to_buy["source"] == "DexScreener":
        pair_id = token_to_buy["pair_id"]
        endpoint = f"latest/dex/pairs/solana/{pair_id}"
        data = await http_client.fetch(base_url, endpoint)
        token_to_buy = parse_by_pair_id(pair_id, data)
    else:
        token_address = token_to_buy["token_address"]
        endpoint = f"tokens/v1/solana/{token_address}"
        data = await http_client.fetch(base_url, endpoint)
        token_to_buy = parse_by_token_address(token_address, data)

    # we checked the token if token has market cap in given range and is not listed on pump or moonshot, we will go and buy it
    if token_to_buy is not None:
        buy_token(token_to_buy)


def parse_by_pair_id(pair_id, data):
    if not isinstance(data, dict) or len(data) == 0:
        print(f"No data found for the pairId: {pair_id}, occurred: {datetime.now()}")
        return None

    token_info = data.get("pairs")[0]
    market_cap = token_info.get("marketCap")
    dex_id = token_info.get("dexId")

    if (market_cap and 10_000 < market_cap < 5_000_000) and (dex_id is not "moonshot" or "pumpfun"):
        # using global variable
        global token_pair_data
        # we add dynamically token address to our dict
        token_pair_data.update({"baseToken": token_info.get("baseToken", {}).get("address")})  # token we want to buy
        return token_pair_data  # return dict
    print(f"market cap is too high/low, pairId: {pair_id}, occurred: {datetime.now()}")
    return None


def parse_by_token_address(token_address, data):
    if not isinstance(data, list) or len(data) == 0:
        print(f"No data found for the pairId: {token_address}, occurred: {datetime.now()}")
        return None

    token_info = data[0]
    market_cap = token_info.get("marketCap")
    dex_id = token_info.get("dexId")

    if (market_cap and 10_000 < market_cap < 5_000_000) and (dex_id is not "moonshot" or "pumpfun"):
        # using global variable
        global token_pair_data
        # we add dynamically token address to our dict
        token_pair_data.update({"baseToken": token_info.get("baseToken", {}).get("address")})  # token we want to buy
        print(token_pair_data)
        return token_pair_data  # return dict
    print(f"market cap is too high/low, pairId: {token_address}, occurred: {datetime.now()}")
    return None
