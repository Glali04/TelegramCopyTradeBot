import re


# it will only track solana addresses, there is the most trade (for my bot eth transactions would be to expensive,
# other blockchains is not that active to worth looking them)
def extract_token_address(text: str):
    # Regex pattern for check if in the text provided a dex URL
    dexscreener_pattern = r"https://dexscreener\.com/solana/([1-9A-HJ-NP-Za-z]+)"

    general_token_address_pattern = r"\b[1-9A-HJ-NP-Za-z]{32,44}$\b"

    dexscreener_match = re.search(dexscreener_pattern, text)
    if dexscreener_match:
        return {
            "pair_id": dexscreener_match.group(1),  # to get the pairId
            "source": "DexScreener"
        }

    general_match = re.search(general_token_address_pattern, text)
    if general_match:
        return {
            "token_address": general_match.group(0),  # to get the token address
            "source": "General token address"
        }

    return None
