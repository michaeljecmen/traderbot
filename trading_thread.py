"""Class module where each threaded object manages the trading of exactly one ticker."""

import datetime
from datetime import timedelta, datetime
import threading
import robin_stocks.robinhood as r
from readerwriterlock import rwlock

from position import OpenPaperPosition, OpenStockPosition
from singletons.market_data import MarketData
from singletons.trade_capper import TradeCapper
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
    trade_capper = {}

    # classwide constants (after initialization)
    take_profit_percent = 0.01
    max_loss_percent = 0.01
    paper_trading = True

    def __init__(self, ticker, market_data, market_time, holdings, buying_power, trade_capper, strategy, take_profit_percent, max_loss_percent, paper_trading=True):
        # safety first when setting class variables
        threading.Thread.__init__(self)
        with self.ctor_lock: # TODO each thread tracks its own stats and they all print together at the end
            # set shared concurrent data
            TradingThread.market_data = market_data
            TradingThread.market_time = market_time
            TradingThread.holdings = holdings
            TradingThread.buying_power = buying_power
            TradingThread.trade_capper = trade_capper
            TradingThread.take_profit_percent = take_profit_percent
            TradingThread.max_loss_percent = max_loss_percent
            TradingThread.paper_trading = paper_trading

        self.ticker = ticker
        self.position = None
        self.strategy = strategy

        # make sure we do not have an open position. 
        # if we do, close it immediately
        

    def run(self):
        print_with_lock("thread {} began".format(self.ticker))
        
        while self.market_time.is_time_left_to_trade():
            self.looking_to_buy()   
            
            # did we leave the looking to buy function because we bought in?
            # or because we ran out of resources? if we ran out, end this thread
            if self.position is None:
                return
            
            # otherwise, we're now looking to sell
            self.looking_to_sell()


    def open_position(self):
        if self.paper_trading:
            self.position = OpenPaperPosition(self.ticker, self.buying_power.spend_and_get_amount(), self.market_data)
        else:
            self.position = OpenStockPosition(self.ticker, self.buying_power.spend_and_get_amount(), self.market_data)


    def close_position(self):
        self.buying_power.add_funds(self.position.close())
        self.position = None

    
    def looking_to_buy(self):
        # if there is no time left or we've made all of our trades or we already have a position
        while self.market_time.is_time_left_to_trade() and self.trade_capper.are_trades_left() and self.position is None:
            if self.strategy.should_buy_on_tick():
                self.open_position()
    

    def looking_to_sell(self):
        open_price = self.position.get_open_price()
        while self.market_time.is_time_left_to_trade() and self.position is not None:
            current_price = self.market_data.get_data_for_ticker(self.ticker)
            if current_price >= open_price * 1+self.take_profit_percent:
                # closing for profit
                self.close_position()
                return
            if current_price <= 1-self.max_loss_percent * open_price:
                # closing for loss
                self.close_position()
                return
        
        # if we are here, that means time left to trade has run out and we have open position -- bad
        self.close_position()
