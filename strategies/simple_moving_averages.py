from strategies.strategy import Strategy
from singletons.market_data import MarketData
from strategies.moving_average import MovingAverage
from utilities import print_with_lock

class SimpleMovingAverages(Strategy):
    """Buy when the short <num_trades> moving average crosses up the long <num_trades>
    moving average for the given ticker."""

    def __init__(self, market_data, ticker, short, long):
        super().__init__(market_data, ticker)
        self.long = long
        self.short = short
        self.short_moving_avg = MovingAverage(market_data, ticker, short)
        self.long_moving_avg = MovingAverage(market_data, ticker, long)
        self.relevant = True

    def should_buy_on_tick(self):
        # update both and buy if we have a higher short than long MA
        self.short_moving_avg.update()
        self.long_moving_avg.update()
        print_with_lock("MA for {}: short={} long={}".format(self.ticker, self.short_moving_avg.get_moving_average(), self.long_moving_avg.get_moving_average()))
        return self.short_moving_avg.get_moving_average() > self.long_moving_avg.get_moving_average()

    def get_name(self):
        return 'SimpleMovingAverages with long={} short={}'.format(self.long, self.short)