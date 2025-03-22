# Loads environment variables and defines bot settings.

from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

# Define settings
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BUY_AMOUNT_IN_US_DOLLAR = os.getenv("BUY_AMOUNT_IN_US_DOLLAR")
