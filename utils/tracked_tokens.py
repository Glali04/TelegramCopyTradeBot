# data which we will stored for each trade
token_pair_data = {
    "baseToken": None,  # token we want to buy
    # address of wrapped sol we want to, receive this when we sell baseToken
    "quoteToken": "So11111111111111111111111111111111111111112",
    "bought": False,  # to know later do we need to buy or sell the token
    # for price tracking, we will put here data from jupiter quote (most reliable data of price we bought this token)
    "on_price_we_bought": None,
}
