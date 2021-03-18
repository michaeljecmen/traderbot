import robin_stocks.robinhood as r

from singletons.market_data import MarketData

from utilities import print_with_lock

class OpenStockPosition:
    """Class used for real trading."""
    def __init__(self, ticker, budget):
        # open the position given the allocated budget
        resp = r.orders.order_buy_fractional_by_price(ticker, budget, timeInForce='gfd', extendedHours=False, jsonify=True)
        print_with_lock("ORDER RESPONSE DICT: ", resp)
        # self.quantity = resp["quantity"]
        # self.open_price = resp["price"]
        self.ticker = ticker
        self.quantity = resp["quantity"]
        self.open_price = resp["price"]
    

    def get_open_price(self):
        return self.open_price


    def close(self):
        # robin_stocks.robinhood.orders.order_sell_fractional_by_quantity(symbol, quantity, timeInForce='gfd', priceType='bid_price', extendedHours=False, jsonify=True)
        # then confirm that sell actually worked
        pass # TODO
    

class OpenPaperPosition:
    """Class used for paper trading."""
    def __init__(self, ticker, budget, market_data):
        # open the position given the allocated budget
        # instead of buying here, just get current price and assume that's what we bought at
        self.open_price = market_data.get_data_for_ticker(ticker)
        self.market_data = market_data
        self.ticker = ticker
        self.quantity = budget/self.open_price


    def get_open_price(self):
        return self.open_price


    def close(self):
        # get price right now to see what we would've sold at
        close_price = self.market_data.get_data_for_ticker(self.ticker)

        print_with_lock("sold {} shares of {} for a net {} of {}".format(
            self.quantity, self.ticker, "gain" if close_price > self.open_price else "loss", close_price-self.open_price))
