import re


# it will only track solana and bsc addresses, there is the most trade (for my bot eth transactions would be to expensive,
# other blockchains is not that active to worth looking them)
def extract_token_address(text: str):
    # Regex pattern for check if in the text provided a dex URL
    dexscreener_pattern = r"https://dexscreener\.com/(solana|bsc)/([1-9A-HJ-NP-Za-z]+|0x[a-fA-F0-9]{40})"

    # General token address pattern (Solana: 32-44 chars, BSC: 42 chars starting with '0x')
    general_token_address_pattern = r"\b(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-z]{32,44})\b"
    bsc_chain_pattern = r"\b(bsc|binance smart chain)\b"

    dexscreener_match = re.search(dexscreener_pattern, text)
    if dexscreener_match:
        return {
            "blockchain": dexscreener_match.group(1),  # to get the blockchain
            "pair_id": dexscreener_match.group(2),  # to get the pairId
            "source": "DexScreener"
        }

    general_match = re.search(general_token_address_pattern, text)
    if general_match:
        found = False
        token_address = general_match.group(1)
        if token_address[0:2] != "0x":
            blockchain = "solana"
            found = True
        else:
            if re.search(bsc_chain_pattern, text, re.IGNORECASE):
                blockchain = "bsc"
                found = True
        if found:
            return {
                "blockchain": blockchain,
                "token_address": token_address,
                "source": "general"
            }
    return None