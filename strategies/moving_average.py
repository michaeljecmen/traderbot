import threading

from singletons.market_data import MarketData, TickerData
from utilities import print_with_lock
from traderbot_exception import ConfigException

class MovingAverage:
    """Simple class for keeping an updated moving average of a given width.
    
    Used for tracking N-day moving averages for stock prices."""
    ctor_lock = threading.Lock()
    market_data = {}

    def __init__(self, market_data, ticker, n):
        with self.ctor_lock:
            MovingAverage.market_data = market_data

        # update self with market info, usually pre-market
        self.n = n
        self.current_moving_avg = 0.0
        self.ticker = ticker
        self.sliding_window = [self.market_data.get_data_for_ticker(self.ticker)]
        self.ind = 1

        # used to determine what, if any, the new data are since the last
        # time we ticked
        self.prev_td_ind = 1

    def calculate_moving_average(self):
        """Calculate and store MA from fully initialized sliding window."""
        assert(self.n == len(self.sliding_window))
        sum_price = 0.0
        for p in self.sliding_window:
            sum_price += p
        self.current_moving_avg = sum_price/self.n

    def get_moving_average(self):
        """Returns the current moving average"""
        return self.current_moving_avg

    def update_moving_average(self, new_data):
        """Updates the sliding window with the new data appended at the 'end'"""
        if self.n == len(self.sliding_window):
            # remove old contribution from item that is soon to be removed
            old_contribution = self.sliding_window[self.ind]/self.n
            new_contribution = new_data/self.n
            self.current_moving_avg = self.current_moving_avg - old_contribution + new_contribution
            self.sliding_window[self.ind] = new_data
            self.ind += 1

            # remember to reset the index to the start of the sliding window if we go off the end
            if self.ind == self.n:
                self.ind = 0
        else:
            # otherwise we aren't at capacity yet, just append to end
            self.sliding_window.append(new_data)
            if self.n == len(self.sliding_window):
                # if we now have enough to calculate the moving average, do it now
                self.calculate_moving_average()

    def update(self):
        """Update moving average with current prices at end of window.
        All new prices since the last time this function was called (determined by
        the location of TickerData::ind """
        # assume that history-len trades did not occur since the last tick
        # see what the ind of TickerData is, then grab all most recent trades since then
        # overstepping boundaries here in the name of fast access
        td = self.market_data.get_ticker_data_for_ticker(ticker)
        if td.ind == self.prev_td_ind:
            return
        
        with td.lock.gen_rlock():
            while self.prev_td_ind != td.ind:
                self.update_moving_average(td.prices[self.prev_td_ind])
                self.prev_td_ind += 1
                if self.prev_td_ind == self.n:
                    self.prev_td_ind = 0
        

