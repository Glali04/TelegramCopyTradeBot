import time
from web3 import Web3
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from utils.bsc_utils.web3_setup import w3, account_address, v2_address, v3_address, v2_router, v3_router
from utils.bsc_utils.bnb_price import get_bnb_price
from utils.bsc_utils.gas_price import get_bsc_gas_price
from utils.bsc_utils.transaction import confirm_transaction, send_transaction, approve_dex, get_token_decimals
from utils.tracked_tokens import bsc_tracked_tokens, TrackedToken
from database.commands import save_trade
from config.settings import BUY_AMOUNT_IN_US_DOLLAR


async def swap_tokens(token: TrackedToken, sell_transaction=True, sell_all=False):
    print("we are in swap")
    # Handles buying and selling tokens.
    if sell_transaction:
        if not token.approved:
            if token.router_version == "v2":
                router_address = v2_address
            else:
                router_address = v3_address
            await approve_dex(token, router_address)
            print("token approved susseccfully")
        amount_to_sell = token.raw_amount if sell_all else token.raw_amount * 0.25

        tx_hash = await execute_swap(token.base_token, token.quote_token, int(amount_to_sell), token.router_version)
    else:
        print("trying to buy")
        bnb_price = await get_bnb_price()
        print(bnb_price)
        amount_in_wei = in_wei(bnb_price)
        print(amount_in_wei)
        tx_hash = await execute_swap(token.quote_token, token.base_token, amount_in_wei, token.router_version)
    if tx_hash:
        received_amount = await confirm_transaction(tx_hash, need_received_amount=True)
        # this means we get back some value so transaction was successful
        if received_amount:
            if sell_transaction:
                token.sold += received_amount
                if sell_all:
                    print("token sold and successfully removed from tracked tokens")
                    bsc_tracked_tokens.remove(token)
                    await save_trade(token.user_name, token.base_token, token.start_time, token.end_time,
                                     token.bought, token.sold, token.exit_reason)
                else:
                    print("sold 25%")
                    token.raw_amount -= int(token.raw_amount * 0.25)  # 25% profit-taking strategy
                return True
            else:
                print("token bought successfully")
                token.raw_amount = received_amount
                token.bought = amount_in_wei
                decimals = await get_token_decimals(token.base_token)
                bought_with = float(BUY_AMOUNT_IN_US_DOLLAR)
                token.buy_price = float(bought_with / (received_amount / (10 ** decimals)))
                print(f"token buy price was: {token.buy_price}")
                bsc_tracked_tokens.append(token)

                timestamp = time.time()
                token.unix_timestamp = timestamp
                token.start_time = timestamp


async def execute_swap(token_in, token_out, amount_in, router_version):
    # Builds and executes a swap transaction on PancakeSwap.
    print("we are executing swap")
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(1)):  # Retry up to 3 times
        with attempt:
            try:
                gas_price = await get_bsc_gas_price()
                print(f"gas {gas_price}")
                latest_block = await w3.eth.get_block('latest') # await the coroutine first
                timestamp = latest_block.get('timestamp', int(time.time())) + 10000 # Now access 'timestamp'
                print(f"timestamp {timestamp}")
                tx_count = await w3.eth.get_transaction_count(account_address, 'pending')
                print(f"tx_count {tx_count}")
                gas_price_in_wei = Web3.to_wei(gas_price, 'gwei')
                print(f"gas_price {gas_price_in_wei}")
                print("we are inside try")
                if router_version == "v2":
                    coroutine_swap_txn = v2_router.functions.swapExactTokensForTokens(
                        amount_in,
                        100000,
                        [token_in, token_out],
                        account_address,
                        timestamp
                    ).build_transaction({
                        'from': account_address,
                        'gasPrice': gas_price_in_wei,
                        'nonce': tx_count
                    })
                    print(f"asd v2, {coroutine_swap_txn}")
                """else:
                    coroutine_swap_txn = v3_router.functions.exactInputSingle({
                        'tokenIn': token_in,
                        'tokenOut': token_out,
                        'fee': 3000,  # Example: 0.3% Uniswap V3 fee tier
                        'recipient': account_address,
                        'deadline': timestamp,
                        'amountIn': amount_in,
                        'amountOutMinimum': 0,  # Set based on slippage tolerance
                        'sqrtPriceLimitX96': 0  # 0 means no limit on price impact
                    }).build_transaction({
                        'from': account_address,
                        'gasPrice': gas_price_in_wei,
                        'nonce': tx_count
                    })
                    print(f"asd v3, {coroutine_swap_txn}")"""
                print("transaction send from swap execute")
                swap_tx = await coroutine_swap_txn
                return await send_transaction(swap_tx)
            except Exception as e:
                print(f"something went wrong retrying {e}")
                raise
    print("something went wrong after all attempts we failed to send transaction")
    return None


# both BSC and Ethereum use similar units for their currencies.
def in_wei(bnb_price):
    amount_in_bnb = float(BUY_AMOUNT_IN_US_DOLLAR) / bnb_price
    return Web3.to_wei(amount_in_bnb, 'ether')
