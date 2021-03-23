
class Strategy:
    """Interface class for trading strategies that the bot uses.
    
    Defines the interface for current and future strategy impls."""
    def __init__(self):
        pass

    def is_relevant(self):
        # strategies are by default relevant, but allow overriding of this method
        # if there is some reason a can determine on construction a ticker is
        # untradeable for the day
        return True
    
    def should_buy_on_tick(self):
        pass