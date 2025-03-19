from utils.client_sessions_to_servers import http_client
from datetime import datetime
from utils.trade_execution import buy_token
from utils.tracked_tokens import TrackedToken

"""first we will fetch data from dexscreener to get all information about the token, that maybe we will buy. 
depending on how the message was sent in the group, we can get various information about the token, the actual ca or 
pair id"""


# if market cap is between defined limit and token is not on pumpfun or moonshot, we will create an instance of
# TrackedToken
async def request_token_information(fetch_token_information: dict, user_id: int):
    # either we will open a client session or we use an already created to this server
    base_url = "https://api.dexscreener.com"

    token_to_buy = None
    if fetch_token_information["source"] == "DexScreener":
        pair_id = fetch_token_information["pair_id"]
        endpoint = f"latest/dex/pairs/solana/{pair_id}"
        data = await http_client.fetch(base_url, endpoint)
        token_to_buy = parse_by_pair_id(pair_id, data)
    else:
        token_address = fetch_token_information["token_address"]
        endpoint = f"tokens/v1/solana/{token_address}"
        data = await http_client.fetch(base_url, endpoint)
        token_to_buy = parse_by_token_address(token_address, data)

    # we checked the token if token has market cap in given range and is not listed on pump or moonshot, we will go
    # and buy it
    if token_to_buy:
        token_to_buy.user_id = user_id
        print("after fetchin token data tracked token looks like this ", token_to_buy)
        await buy_token(token_to_buy)


def parse_by_pair_id(pair_id, data):
    if not isinstance(data, dict) or len(data) == 0:
        print(f"No data found for the pairId: {pair_id}, occurred: {datetime.now()}")
        return None

    token_info = data.get("pairs")[0]
    market_cap = token_info.get("marketCap")
    dex_id = token_info.get("dexId")

    print("token was found via dex")
    if (market_cap and 25_000 < market_cap < 5_000_000) and (dex_id not in ["pumpfun", "moonshot"]):
        print("market cap was right", market_cap)
        return TrackedToken(token_info.get("baseToken", {}).get("address"))
    print(f"market cap is too high/low, pairId: {pair_id}, occurred: {datetime.now()}")
    return None


def parse_by_token_address(token_address, data):
    if not isinstance(data, list) or len(data) == 0:
        print(f"No data found for the pairId: {token_address}, occurred: {datetime.now()}")
        return None

    print("token was found via ca")
    token_info = data[0]
    market_cap = token_info.get("marketCap")
    dex_id = token_info.get("dexId")

    if (market_cap and 25_000 < market_cap < 5_000_000) and (dex_id not in ["pumpfun", "moonshot"]):
        print("market cap was right", market_cap)
        return TrackedToken(token_address)
    print(f"market cap is too high/low, pairId: {token_address}, occurred: {datetime.now()}")
    return None
