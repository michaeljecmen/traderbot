"""Class module where each threaded object manages the trading of exactly one ticker."""

import datetime
from datetime import timedelta, datetime
import threading
import robin_stocks.robinhood as r
from readerwriterlock import rwlock

from position import OpenPaperPosition, OpenStockPosition
from market_data import MarketData
from utilities import print_with_lock
import strategies.long_vs_short_moving_average

class TradingThread (threading.Thread):
    # lock to keep everything in order during construction
    ctor_lock = threading.Lock()

    # these must be reader locked. they are updated by the outer thread
    holdings = {}
    market_data = {}
    market_time = {}
    buying_power = {}

    # classwide constants (after initialization)
    take_profit_percent = 0.01
    max_loss_percent = 0.01
    paper_trading = True

    # TODO confirm via pythonlvalues that these are actually 1 per class (lock is same for all objects)

    def __init__(self, ticker, market_data, market_time, holdings, buying_power, strategy, take_profit_percent, max_loss_percent, paper_trading=True):
        # safety first when setting class variables
        threading.Thread.__init__(self)
        with self.ctor_lock:
            # set shared concurrent data
            TradingThread.market_data = market_data
            TradingThread.market_time = market_time
            TradingThread.holdings = holdings
            TradingThread.buying_power = buying_power
            TradingThread.take_profit_percent = take_profit_percent
            TradingThread.max_loss_percent = max_loss_percent
            TradingThread.paper_trading = paper_trading

        self.ticker = ticker
        self.position = None
        self.strategy = strategy

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
        self.looking_to_buy()   
        
        # if no time left:
        # robin_stocks.robinhood.orders.cancel_all_stock_orders()
        # and also sell if open position


    def open_position(self):
        print_with_lock("opening position for {}".format(self.ticker))
        if self.paper_trading:
            self.position = OpenPaperPosition(ticker, self.buying_power.spend_and_get_amount(), self.market_data)
        else:
            self.position = OpenStockPosition(ticker, self.buying_power.spend_and_get_amount(), self.market_data)


    def close_position(self):
        self.position.close()
        self.position = None

    
    def looking_to_buy(self):
        while self.market_time.is_time_left_to_trade() and self.position is None:
            if self.strategy.should_buy_on_tick():
                self.open_position()
    

    def looking_to_sell(self):
        open_price = self.position.get_open_price()
        while self.market_time.is_time_left_to_trade() and self.position is not None:
            current_price = self.market_data.get_data_for_ticker(self.ticker)
            if current_price >= open_price * 1+self.take_profit_percent:
                # closing for profit
                self.position.close()
                return
            if current_price <= 1-self.max_loss_percent * open_price:
                # closing for loss
                self.position.close()
                return
        
        # if we are here, that means time left to trade has run out and we have open position -- bad
        self.close_position()
