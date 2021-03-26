from datetime import timedelta, datetime

from readerwriterlock import rwlock

from utilities import print_with_lock

class TradeCapper:
    """Threadsafe class for concurrent reads and writes to the 
    number of trades left in a market day. Should be a singleton."""
    
    def __init__(self, max_trades_per_day):
        self.lock = rwlock.RWLockWrite()

        if max_trades_per_day is None:
            # no cap on trading
            self.num_trades_left_today = float('inf')
            return

        # decrement this value eagerly until zero
        self.num_trades_left_today = max_trades_per_day

    def make_trade(self):
        with self.lock.gen_wlock():
            # eagerly reserve the trade it will take to sell this stock
            # because we always sell before day end
            self.num_trades_left_today -= 2

    def are_trades_left(self):
        with self.lock.gen_rlock():
            return self.num_trades_left_today >= 2

