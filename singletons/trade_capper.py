from datetime import timedelta, datetime

from threading import Lock

from utilities import print_with_lock

class TradeCapper:
    """Threadsafe class for concurrent reads and writes to the 
    number of trades left in a market day. Should be a singleton."""
    
    def __init__(self, max_trades_per_day):
        self.lock = Lock()

        # decrement this value eagerly until zero
        self.num_trades_left_today = max_trades_per_day

    def ask_for_trade(self):
        with self.lock:
            if self.num_trades_left_today < 2:
                return False
            
            # eagerly reserve the trade it will take to sell this stock
            # because we always sell before day end
            self.num_trades_left_today -= 2
            return True
