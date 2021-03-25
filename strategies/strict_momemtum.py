"""Follows the following basic trend: it is a good time to buy
if the standard deviation of the last N trades is more than <PERCENT>% of the mean,
which would mean that the price has moved significantly more violently than
1% in the last N trades. If this is true, and the current trend is up, buy in."""

import threading

from strategies.strategy import Strategy
from utilities import print_with_lock

class StrictMomentum(Strategy):
    market_data = {}
    ctor_lock = threading.Lock()
    def __init__(self, market_data, ticker, percent):
        """Pass percent as a number in the range (0,100], for 5% pass 5, not .05"""
        super().__init__()
        with self.ctor_lock:
            StrictMomentum.market_data = market_data
        self.percent = percent/100.0
        self.ticker = ticker

        
    def should_buy_on_tick(self):
        mean, stddev, trend = self.market_data.get_trend_for_ticker(self.ticker)
        if trend != "up":
            return False
        
        # if standard deviation is more than <PERCENT>% of stock price and trending up, good buy
        return stddev >= mean*self.percent
        