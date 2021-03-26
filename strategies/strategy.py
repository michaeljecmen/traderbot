import threading

class Strategy:
    """Base class for trading strategies that the bot uses.
    
    Defines the interface for current and future strategy impls,
    and stores some shared data, like the market data reference
    and the ticker that each strategy tracks."""
    ctor_lock = threading.Lock()
    market_data = {}
    def __init__(self, market_data, ticker):
        with self.ctor_lock:
            Strategy.market_data = market_data
        self.ticker = ticker

    def is_relevant(self):
        # strategies are by default relevant, but allow overriding of this method
        # if there is some reason a can determine on construction a ticker is
        # untradeable for the day
        return True
    
    def should_buy_on_tick(self):
        return False
    
    def get_name(self):
        return 'Strategy'