from strategies.strategy import Strategy
from market_data import MarketData
from moving_average import MovingAverage

# TODO put one of these in each tradingthread object
class LongShortMovingAverage(Strategy):
    """Buy when the short day moving average crosses up the long day 
    moving average for the given ticker."""

    def __init__(self, market_data, ticker, short, long):
        self.short_moving_avg = MovingAverage(market_data, ticker, short)
        self.long_moving_avg = MovingAverage(market_data, ticker, long)


    def should_buy_on_tick(self):
        old_short = self.short_moving_avg.get_moving_average()
        old_long = self.long_moving_avg.get_moving_average()
        if old_short > old_long:
            # short already crossed up long, don't bite
            return False

        # otherwise update both and buy if we now have a higher short than long MA
        self.short_moving_avg.update()
        self.long_moving_avg.update()
        return self.short_moving_avg.get_moving_average() > self.long_moving_avg.get_moving_average()

