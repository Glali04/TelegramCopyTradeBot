# data which we will be stored for each trade
# here we will store open trades
tracked_tokens = []


class TrackedToken:
    """Represents a token that is being monitored."""

    def __init__(self, base_token):
        # this data we need to be able to automatize token swap and program will automatically know when to sell
        self.base_token: str = base_token
        self.quote_token = "So11111111111111111111111111111111111111112"
        self.buy_price: float = None
        self.raw_amount: int = None
        self.ath_price: float = None
        self.unix_timestamp: float = None
        # data we need for database for later analyses (from above we will use base_token)
        self.user_id: int = None
        self.start_time: float = None # the timestamp we bought token
        self.end_time: float = None # the timestamp we sold entire bag of token
        self.bought: int  # amount of lamports we bought this token
        self.sold: int = 0  # amount of lamports we get for selling this token
        self.exit_reason: str = None # look up while this trade ended
        """We need unit_timestamp because i want to sell the token if for 20 minutes is not set for it new ath and we did
        no sell it yet, i need it to save cu(compute units) and to do not reduce as much as i can active trade list"""
