"""Class module where each threaded object manages the trading of exactly one ticker."""

import datetime
from datetime import timedelta, datetime
import threading

class TradingThread (threading.Thread):
    # these values will be overwritten during first thread construction
    ZERO_TIME = timedelta()
    END_OF_DAY = ""
    time_until_close = ""
    time_lock = threading.Lock()
    # TODO confirm via lvalues that these are actually 1 per class (lock is same for all objects)

    def __init__(self, ticker, eod_time):
        # safety first when setting class variables
        threading.Thread.__init__(self)
        self.time_lock.acquire()

        self.ticker = ticker
        now = datetime.now()
        TradingThread.END_OF_DAY = datetime(now.year, now.month, now.day, eod_time.hour, eod_time.minute, eod_time.second, eod_time.microsecond)
        # TODO determine if we have an open position and set a bool
        # would be a mistake but should be defensive here
        # also should have a position member, easier than calling RH api each time
        self.update_time_left_to_trade()

        self.time_lock.release()


    def run(self):
        # TODO call the correct function based on whether or not we have an open position
        with self.time_lock:
            print("thread {} began".format(self.ticker))


    def close_position(self):
        # TODO close the position
        pass

    
    def looking_to_buy(self):
        while True:
            pass
    

    def looking_to_sell(self):
        while True:
            pass
    

    def update_time_left_to_trade(self):
        # this function assumes ownership of time_lock
        TradingThread.time_until_close = self.END_OF_DAY - datetime.now()


    def is_time_left_to_trade(self):
        # not too shabby python RAII
        with self.time_lock:
            # read first, if no time already then don't bother writing
            if self.time_until_close <= self.ZERO_TIME:
                return False

            # otherwise update the time for everybody
            self.update_time_left_to_trade()
            return True
