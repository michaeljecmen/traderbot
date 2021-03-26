import threading

import robin_stocks.robinhood as r

from singletons.market_data import MarketData
from utilities import print_with_lock

class DayMovingAverage:
    """Simple class for keeping an updated moving average of a given width.
    
    Used for tracking N-day moving averages for stock prices."""
    ctor_lock = threading.Lock()
    market_data = {}

    def __init__(self, market_data, ticker, n, interval='day'):
        with self.ctor_lock:
            DayMovingAverage.market_data = market_data

        # update self with market info, usually pre-market
        self.n = n
        self.current_moving_avg = 0.0
        self.ticker = ticker

        # get data for a year then whittle down
        data_for_last_n_intervals = r.stocks.get_stock_historicals(ticker, interval=interval, span='year')

        # get the last n intervals from the previous year
        data_for_last_n_intervals = data_for_last_n_intervals[-n:]

        # data is currently in the following format: 
        # a list of n dictionaries with the structure:
        # {     
        #       'begins_at': '2021-03-05T00:00:00Z',
        #       'close_price': '3000.460000',
        #       'high_price': '3009.000000',
        #       'interpolated': False,
        #       'low_price': '2881.000100',
        #       'open_price': '3005.000000',
        #       'session': 'reg',
        #       'symbol': 'AMZN',
        #       'volume': 5388551
        # }
        # so we just want the close price to use as our data
        self.sliding_window = [ float(daily_stats['close_price']) for daily_stats in data_for_last_n_intervals ]
        self.calculate_moving_average()
        print_with_lock("{} {} {} moving avg: {}".format(ticker, n, interval, self.current_moving_avg))

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
        # constant time solution:
        # [a b c d e]
        # avg is (a+b+c+d+e)/n = a/n + b/n + c/n + d/n + e/n
        # so remove ei/n and add e(i+1)/n to get new MA
        old_contribution = self.sliding_window[-1]/self.n
        new_contribution = self.market_data.get_data_for_ticker(ticker)/self.n
        self.current_moving_avg = self.current_moving_avg - old_contribution + new_contribution
        self.sliding_window[-1] = self.market_data.get_data_for_ticker(ticker)

