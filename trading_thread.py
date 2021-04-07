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
from traderbot_exception import TraderbotException

class TradingThread (threading.Thread):
    # lock to keep everything in order during construction
    ctor_lock = threading.Lock()

    # true constants -- don't buy with less than 1 dollar
    BUDGET_THRESHHOLD = 1.00

    # these must be reader locked. they are updated by the outer thread
    market_data = {}
    market_time = {}
    buying_power = {}
    trade_capper = {}
    reports = {}

    # classwide constants (after initialization)
    take_profit_percent = 0.01
    max_loss_percent = 0.01
    paper_trading = True

    def __init__(self, ticker, market_data, market_time, buying_power, trade_capper, strategy, reports, take_profit_percent, max_loss_percent, paper_trading=True):
        # safety first when setting class variables
        threading.Thread.__init__(self)
        with self.ctor_lock:
            # set shared concurrent data
            TradingThread.market_data = market_data
            TradingThread.market_time = market_time
            TradingThread.buying_power = buying_power
            TradingThread.trade_capper = trade_capper
            TradingThread.take_profit_percent = take_profit_percent
            TradingThread.max_loss_percent = max_loss_percent
            TradingThread.paper_trading = paper_trading
            TradingThread.reports = reports

        self.ticker = ticker
        self.position = None
        self.strategy = strategy

        # will be overridden on run()
        self.init_time = datetime.now()

        # tracks the following information:
        # {
        #     "open_time": <timestamp>,
        #     "close_time": <timestamp>,
        #     "quantity": <quantity>,
        #     "open_price": <price>,
        #     "close_price": <price>
        # }
        self.statistics = []

        # net profit/loss
        self.net = 0.0
        
    def run(self):
        self.init_time = datetime.now()
        print_with_lock("thread {} began".format(self.ticker))
        
        while self.market_time.is_time_left_to_trade():
            self.looking_to_buy()   
            
            # did we leave the looking to buy function because we bought in?
            # or because we ran out of resources? if we ran out, end this thread
            if self.position is None:
                return
            
            # otherwise, we're now looking to sell
            self.looking_to_sell()
        
        # end of the line for us, generate our report
        self.generate_report()

    def open_position(self):
        # do not buy if we're out of funds!
        budget = self.buying_power.spend_and_get_amount()
        if budget < self.BUDGET_THRESHHOLD:
            # don't make trades for under a certain threshhold
            return
        if self.paper_trading:
            # if the order timed out or was rejected for some other reason
            # then try again when next relevant
            try:
                self.position = OpenPaperPosition(self.ticker, budget, self.market_data)
            except TraderbotException as te:
                print_with_lock("open position exception:", str(te))
                self.position = None
                return
        else:
            try:
                self.position = OpenStockPosition(self.ticker, budget)
            except TraderbotException as te:
                print_with_lock("open position exception:", str(te))
                self.position = None
                return
        
        # update statistics
        self.statistics.append({
            "open_time": datetime.now(),
            "quantity": self.position.get_quantity(),
            "open_price": self.position.get_open_price(),
            "close_time": -1,
            "close_price": -1
        })

    def close_position(self):
        close_price = 0.0
        try:
            close_price = self.position.close()
        except TraderbotException as te:
            print_with_lock("close position exception:", str(te))
            return
        ts = datetime.now()
        qty = self.position.get_quantity()
        self.buying_power.add_funds(close_price*qty)

        # update statistics
        self.statistics[-1]["close_time"] = ts
        self.statistics[-1]["close_price"] = close_price
        self.net += ((close_price - self.position.get_open_price()) * self.position.get_quantity())
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
            if current_price <= 1-self.max_loss_percent * open_price:
                # closing for loss
                self.close_position()
        
        if self.position is not None:
            # if we are here, that means time left to trade has run out and we have open position -- bad
            self.close_position()

    def generate_report(self):
        """Generates a report regarding this thread's success throughout the day.
        Adds that report to the shared reports object."""
        # ticker
        # strategy
        # net
        # first and last price seen
        # how long traded for
        # how long held for
        # total trades (1 open plus 1 close = 1 trade)
        # total unprofitable trades
        # total profitable trades
        # total neutral trades
        # profit percent
        # best trade
        # worst trade
        last = self.market_data.get_data_for_ticker(self.ticker)
        eod_time = datetime.now()
        first = self.market_data.get_first_price_of_day_for_ticker(self.ticker)
        num_profitable = 0
        num_unprofitable = 0
        num_neutral = 0
        for stat in self.statistics:
            if stat['close_price'] > stat['open_price']:
                num_profitable += 1
            elif stat['close_price'] < stat['open_price']:
                num_unprofitable += 1
            else:
                num_neutral += 1
        

        report = {
            "ticker": self.ticker,
            "strategy": self.strategy.get_name(),
            "traderbot net performance": self.net,
            "total thread lifetime": str(eod_time - self.init_time),
            "total trades made": len(self.statistics),
            "total profitable trades": num_profitable,
            "total unprofitable trades": num_unprofitable,
            "total neutral trades": num_neutral,
            "first price seen": first,
            "last price seen": last,
            "stock net performance": last-first,
        }

        if len(self.statistics) != 0:

            report["first position opened at"] = str(self.statistics[0]['open_time'].time())
            report["last position closed at"] = str(self.statistics[-1]['close_time'].time())

            def add_times(s1, mic1, s2, mic2):
                secs = s1 + s2
                micros = mic1 + mic2
                secs += micros / 1000000
                micros = micros % 1000000
                return secs, micros

            time_held_secs = 0.0
            time_held_micros = 0.0
            best_stat = self.statistics[0]
            worst_stat = best_stat
            best = self.statistics[0]['close_price'] - self.statistics[0]['open_price']
            worst = best
            for stat in self.statistics:
                # timedelta sucks, write our own time adder
                td = stat['close_time'] - stat['open_time']
                time_held_secs, time_held_micros = add_times(time_held_secs, time_held_micros, td.seconds, td.microseconds)

                # also of course find best and worst trade
                margin = stat['close_price'] - stat['open_price']
                if margin > best:
                    best = margin
                    best_stat = stat
                if margin < worst:
                    worst = margin
                    worst_stat = stat

            time_held = timedelta(seconds=time_held_secs, microseconds=time_held_micros)
            report["time held for"] = str(time_held)

            # avoid the strange bug where best and worst trade are same
            # so we call .time() on a string in report["worst trade"]["open_time"].time()
            if abs(best - worst) > .001:
                report["best trade"] = best_stat
                report["best trade"]["open_time"] = str(report["best trade"]["open_time"].time())
                report["best trade"]["close_time"] = str(report["best trade"]["close_time"].time())
                report["best trade"]["net_profit"] = best
                report["worst trade"] = worst_stat
                report["worst trade"]["open_time"] = str(report["worst trade"]["open_time"].time())
                report["worst trade"]["close_time"] = str(report["worst trade"]["close_time"].time())
                report["worst trade"]["net_profit"] = worst
        
        self.reports.add_eod_report(report)
