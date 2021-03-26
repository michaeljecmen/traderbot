from strategies.strategy import Strategy
from singletons.market_data import MarketData
from strategies.day_moving_average import DayMovingAverage
from utilities import print_with_lock

class HistoricalMovingAverage(Strategy):
    """Buy when the short day moving average crosses up the long day 
    moving average for the given ticker."""

    def __init__(self, market_data, ticker, short, long):
        super().__init__(market_data, ticker)
        self.long = long
        self.short = short
        self.short_moving_avg = DayMovingAverage(market_data, ticker, short)
        self.long_moving_avg = DayMovingAverage(market_data, ticker, long)
        self.relevant = True

        # if short already crossed up long, cancel this thread
        if self.short_moving_avg.get_moving_average() > self.long_moving_avg.get_moving_average():
            self.relevant = False

    def is_relevant(self):
        return self.relevant

    def should_buy_on_tick(self):
        # update both and buy if we have a higher short than long MA
        self.short_moving_avg.update()
        self.long_moving_avg.update()
        print_with_lock("MA for {}: short={} long={}".format(self.ticker, self.short_moving_avg.get_moving_average(), self.long_moving_avg.get_moving_average()))
        return self.short_moving_avg.get_moving_average() > self.long_moving_avg.get_moving_average()

    def get_name(self):
        return 'HistoricalMovingAverage with long={} short={}'.format(self.long, self.short)