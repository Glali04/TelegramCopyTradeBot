import asyncio

from hexbytes import HexBytes
from web3 import Web3, exceptions
from utils.bsc_utils.web3_setup import w3, account_address, TOKEN_CONTRACT_ABI
from utils.tracked_tokens import TrackedToken
from utils.bsc_utils.gas_price import get_bsc_gas_price


async def send_transaction(tx):
    # Signs and sends a raw transaction.
    print("sending the transaction")
    txn_hash = await w3.eth.send_transaction(tx)
    print(txn_hash)
    return txn_hash


async def confirm_transaction(tx_hash, need_received_amount = False):
    # Waits for transaction confirmation and returns received token amount.
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash, timeout=25, poll_latency=0.5)
    print(receipt)
    try:
        if receipt.status == 1:
            print(f"✅ Transaction {tx_hash} confirmed!")

            transfer_event_signature = Web3.keccak(text="Transfer(address,address,uint256)").hex()
            # Find the Transfer log
            if need_received_amount:
                for log in receipt.logs:
                    if log.topics[0].hex() == transfer_event_signature:
                        # Extract the indexed parameters from topics, this is the address of receiver
                        to_address = Web3.to_checksum_address("0x" + log.topics[2].hex()[-40:])
                        if to_address == account_address:
                            # Extract the non-indexed parameters from data (value)
                            raw_data = HexBytes(log.data)
                            value = int.from_bytes(raw_data[:32], byteorder="big",
                                                   signed=False)  # 'value' is typically 32 bytes
                            # the value store the amount of tokens we received either from buy or sell transaction
                            return value
            return True
        elif receipt.status == 0:
            print("something went wrong transaction is not added to the block, it is failed")
            return None
    except exceptions.TimeExhausted:
        print("the transaction is not added to the block for 15 seconds")
    except Exception as e:
        print(f"something went wrong: {e}")
    return None


async def approve_dex(token: TrackedToken, router_address):
    """Approve the router to spend tokens on your behalf."""
    token_contract = w3.eth.contract(address=token.base_token, abi=TOKEN_CONTRACT_ABI)
    print("started approving token amount")
    try:
        gas_price = await get_bsc_gas_price()
        approve_txn = await token_contract.functions.approve(router_address, token.raw_amount
                                                             ).build_transaction({
            "from": account_address,
            "gasPrice": Web3.to_wei(gas_price, "gwei"),
            "nonce": await w3.eth.get_transaction_count(account_address)
        })

        tx_hash = await send_transaction(approve_txn)
        if tx_hash:
            print(tx_hash)
            receipt = await confirm_transaction(tx_hash)
            if receipt:
                token.approved = True
                return receipt

    except Exception as e:
        print(f"⚠️ Approval error: {e}")
        return False


async def get_allowance(owner, spender, token: TrackedToken = None):
    """Check the allowance for a token."""
    token_contract = w3.eth.contract(address=token.base_token, abi=TOKEN_CONTRACT_ABI)
    allowance = await token_contract.functions.allowance(owner, spender).call()
    return allowance


async def get_token_decimals(token_address):
    token_contract = w3.eth.contract(address=token_address, abi= TOKEN_CONTRACT_ABI)
    decimals = await token_contract.functions.decimals().call()
    return decimals