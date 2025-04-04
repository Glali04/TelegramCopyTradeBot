# Loads environment variables and defines bot settings.

from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

# Define settings
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BUY_AMOUNT_IN_US_DOLLAR = os.getenv("BUY_AMOUNT_IN_US_DOLLAR")
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
PRIVATE_KEY = os.getenv("BSC_PRIVATE_KEY")
BSC_RPC_URL = "https://bsc-dataseed1.binance.org/"


#i will store here also constants which i need more then one place in my project
headers_for_solana = {
    "accept": "application/json",
    "x-chain": "solana",
    "X-API-KEY": "7f7741539b5f480680daecaf6fe7d1f1"
}

headers_for_bsc = {
    "accept": "application/json",
    "x-chain": "bsc",
    "X-API-KEY": "7f7741539b5f480680daecaf6fe7d1f1"
}
