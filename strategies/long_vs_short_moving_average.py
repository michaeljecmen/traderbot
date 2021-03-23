from strategies.strategy import Strategy
from singletons.market_data import MarketData
from strategies.moving_average import MovingAverage
from utilities import print_with_lock

class LongShortMovingAverage(Strategy):
    """Buy when the short day moving average crosses up the long day 
    moving average for the given ticker."""

    def __init__(self, market_data, ticker, short, long):
        super().__init__()
        self.short_moving_avg = MovingAverage(market_data, ticker, short)
        self.long_moving_avg = MovingAverage(market_data, ticker, long)
        self.relevant = True

        # if short already crossed up long, cancel this thread
        if self.short_moving_avg.get_moving_average() > self.long_moving_avg.get_moving_average():
            self.relevant = False
    

    def is_relevant(self):
        return self.relevant


    def should_buy_on_tick(self):
        old_short = self.short_moving_avg.get_moving_average()
        old_long = self.long_moving_avg.get_moving_average()
        if old_short > old_long:
            # short already crossed up long, don't bite
            return False

        # otherwise update both and buy if we now have a higher short than long MA
        self.short_moving_avg.update()
        self.long_moving_avg.update()
        print_with_lock("MA for {}: short={} long={}".format(self.ticker, self.short_moving_avg.get_moving_average(), self.long_moving_avg.get_moving_average()))
        return self.short_moving_avg.get_moving_average() > self.long_moving_avg.get_moving_average()

