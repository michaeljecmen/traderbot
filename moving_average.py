import threading

import robin_stocks.robinhood as r

from market_data import MarketData
from utilities import print_with_lock

class MovingAverage:
    """Simple class for keeping an updated moving average of a given width.
    
    Used for tracking N-day moving averages for stock prices."""
    ctor_lock = threading.Lock()
    market_data = {}

    def __init__(self, market_data, ticker, n, span="days"):
        with self.ctor_lock:
            MovingAverage.market_data = market_data

        # update self with market info, usually pre-market
        self.n = n
        self.current_moving_avg = 0.0
        self.ticker = ticker

        self.sliding_window = r.stocks.get_stock_historicals(ticker, interval='hour', span='week', bounds='regular', info=None)
        self.calculate_moving_average()
        print_with_lock("curr sliding window for {}:".format(ticker), self.sliding_window)
        print_with_lock("curr moving avg for {}: {}".format(ticker, self.current_moving_avg))

        # important -- update the sliding window with the current price at the end
        # this allows us to update the curr moving average once the market opens
        # by simply replacing the last value in the sliding window with the current
        # market price
        self.sliding_window.append(self.market_data.get_data_for_ticker(ticker))
        self.sliding_window = self.sliding_window[1:]
        # equally important -- do not actually update the market value yet
        # as this is likely a duplicate of the previous closing price from yesterday,
        # don't want to overweight this until the day actually starts and 
        # prices actually start moving


    def calculate_moving_average(self):
        """Calculate and store MA from initialized sliding window."""
        assert(self.n == len(self.sliding_window))
        sum_price = 0.0
        for p in self.sliding_window:
            sum_price += p
        self.current_moving_avg = sum_price/self.n


    def get_moving_average(self):
        """Returns the current moving average"""
        return self.current_moving_avg


    def update(self):
        """Update moving average with current price at end of window."""
        self.sliding_window[-1] = self.market_data.get_data_for_ticker(ticker)
        # TODO could be a better way of doing this, find the O(1) soln
        self.calculate_moving_average()