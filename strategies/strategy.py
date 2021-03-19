
class Strategy:
    """Interface class for trading strategies that the bot uses.
    
    Defines the interface for current and future strategy impls."""
    def __init__(self):
        pass
    
    def should_buy_on_tick(self):
        pass