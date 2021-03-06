"""Strategy module which opens when the price is <percent>% below the mean and not trending down."""

from strategies.strategy import Strategy

class MeanReversion(Strategy):
    def __init__(self, market_data, ticker, percent):
        super().__init__(market_data, ticker)
        self.percent = percent/100.0

    def should_buy_on_tick(self):
        curr_price = self.market_data.get_data_for_ticker(self.ticker)
        mean, stddev, trend = self.market_data.get_trend_for_ticker(self.ticker)

        if trend == "down":
            return False

        # otherwise trending up, just check if price is X% below mean
        # 5% below mean is 95% of mean, if curr price is below that we're in
        return curr_price < mean*(1-self.percent)

    def get_name(self):
        return 'MeanReversion with percent={}'.format(self.percent)