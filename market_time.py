from datetime import timedelta, datetime

from readerwriterlock import rwlock

class MarketTime:
    """Threadsafe class for concurrent reads and writes to the 
    time left in market day for trading. Should be a singleton."""
    
    def __init__(self, end_of_day):
        self.lock = rwlock.RWLockWrite()
        self.END_OF_DAY = end_of_day
        self.ZERO_TIME = timedelta()
        self.time_until_close = 0
        self.update()

    def update(self):
        """Update time left to trade for this and all tradingthread objects."""
        with self.lock.gen_wlock():
            self.time_until_close = self.END_OF_DAY - datetime.now()
        
        # for debugging purposes only
        self.print_time()
    
    def is_time_left_to_trade(self):
        # not too shabby python RAII
        with self.lock.gen_rlock():
            return self.time_until_close > self.ZERO_TIME

    def print_time(self):
        print("---- MARKET TIME ----")
        print("time until close:", self.time_until_close)
        print("---------------------")
