# data which we will be stored for each trade
# here we will store open trades separately for blockchains
solana_tracked_tokens = []
bsc_tracked_tokens = []


class TrackedToken:
    """Represents a token that is being monitored."""

    def __init__(self, base_token):
        # this data we need to be able to automatize token swap and program will automatically know when to sell
        self.base_token: str = base_token
        self.quote_token: str = None  # here we store wsol and wbnb for trading (depending on which chain we are)
        self.buy_price: float = None
        self.raw_amount: int = None
        self.ath_price: float = None
        self.unix_timestamp: float = None
        self.reached_30_precentage_profit: bool = False
        self.approved: bool = False  # on bsc network we need to give approves for dexs router contract to spend
        # specified amount of given token on your behalf

        self.router_version: str = None  # this field we only need for bsc tokens when we fetch token data from dex we
        # will also get from there which router version we need to use for pancakeswap

        # data we need for database for later analyses (from above we will use base_token)
        self.user_name: str = None
        self.start_time: float = None  # the timestamp we bought token
        self.end_time: float = None  # the timestamp we sold entire bag of token
        self.bought: int  # amount of lamports/bnb we bought this token
        self.sold: int = 0  # amount of lamports/bnb we get for selling this token
        self.exit_reason: str = None  # look up while this trade ended
        """We need unit_timestamp because i want to sell the token if for 20 minutes is not set for it new ath and we did
        no sell it yet, i need it to save cu(compute units) and to do not reduce as much as i can active trade list"""
