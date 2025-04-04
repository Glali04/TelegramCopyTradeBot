import json
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware, SignAndSendRawMiddlewareBuilder
from eth_account import Account
from config.settings import PRIVATE_KEY, BSC_RPC_URL

# Load ABI
with open("utils/bsc_utils/abis/v2_router_abi.json", "r") as v2_file:
    V2_ROUTER_ABI = json.load(v2_file)

with open("utils/bsc_utils/abis/v3_router_abi.json", "r") as v3_file:
    V3_ROUTER_ABI = json.load(v3_file)

with open("utils/bsc_utils/abis/token_contract_abi.json", "r") as token_file:
    TOKEN_CONTRACT_ABI = json.load(token_file)

# initialize web3
w3 = AsyncWeb3(AsyncHTTPProvider(BSC_RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Load Account
account = Account.from_key(PRIVATE_KEY)
account_address = account.address
w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(account), layer=0)
w3.eth.default_account = account.address


# Load Routers
v2_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
v3_address = "0x1b81D678ffb9C0263b24A97847620C99d213eB14"
v2_router = w3.eth.contract(address=v2_address, abi=V2_ROUTER_ABI)
v3_router = w3.eth.contract(address=v3_address, abi=V3_ROUTER_ABI)
