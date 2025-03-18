# data which we will be stored for each trade
#here we will store open trades
tracked_tokens = []

class TrackedToken:
    """Represents a token that is being monitored."""
    def __init__(self, base_token):
        # this data we need to be able to automatize token swap and program will automatically know when to sell
        self.base_token: base_token
        self.quote_token: "So11111111111111111111111111111111111111112"
        self.buy_price: None
        self.raw_amount: None
        self.ath_price: None
        self.unix_timestamp: None
        # data we need for database for later analyses (from above we will use base_token)
        self.user_id: None
        self.start_time: None # the timestamp we bought token
        self.end_time: None # the timestamp we sold entire bag of token
        self.bought: None # amount of lamports we bought this token
        self.sold: None # amount of lamports we get for selling this token
        self.exit_reason: None # look up while this trade ended
        """We need unit_timestamp because i want to sell the token if for 20 minutes is not set for it new ath and we did
        no sell it yet, i need it to save cu(compute units) and to do not reduce as much as i can active trade list"""