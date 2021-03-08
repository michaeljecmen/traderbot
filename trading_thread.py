"""Class module where each threaded object manages the trading of exactly one ticker."""

import datetime
from datetime import timedelta, datetime
import threading
import robin_stocks.robinhood as r
from readerwriterlock import rwlock

from market_data import MarketData
from utilities import print_with_lock

class TradingThread (threading.Thread):
    # lock to keep everything in order during construction
    ctor_lock = threading.Lock()

    # these must be reader locked. they are updated by the outer thread
    holdings = {}
    market_data = {}
    market_time = {}
    # TODO confirm via pythonlvalues that these are actually 1 per class (lock is same for all objects)

    def __init__(self, ticker, market_data, market_time, holdings):
        # safety first when setting class variables
        threading.Thread.__init__(self)
        with self.ctor_lock:
            self.ticker = ticker
            self.position = None

            # set shared concurrent data
            TradingThread.market_data = market_data
            TradingThread.market_time = market_time
            TradingThread.holdings = holdings

            self.currently_holding = self.is_position_open_check()
            # TODO determine if we have an open position and set a bool
            # would be a mistake but should be defensive here
            # also should have a position member, easier than calling RH api each time


    def is_position_open_check(self):
        if self.position is not None:
            return True
        return False # TODO read from holdings and compare to None


    def run(self):
        with self.ctor_lock:
            print_with_lock("thread {} began".format(self.ticker))
        # TODO call the correct function based on whether or not we have an open position
        if self.market_time.is_time_left_to_trade():
            with self.ctor_lock:
                print_with_lock("thread {} trading!".format(self.ticker))
        
        # if no time left:
        # robin_stocks.robinhood.orders.cancel_all_stock_orders()
        # and also sell if open position


    def open_position(self):
        # TODO
        
        pass


    def close_position(self):
        # TODO close the position
        # when selling, confirm that all was sold via api
        # robin_stocks.robinhood.orders.order_sell_fractional_by_quantity(symbol, quantity, timeInForce='gfd', priceType='bid_price', extendedHours=False, jsonify=True)
        self.position = None

    
    def looking_to_buy(self):
        # TODO
        while self.is_time_left_to_trade():
            pass
    

    def looking_to_sell(self):
        # TODO
        while self.is_time_left_to_trade():
            pass
