import robin_stocks.robinhood as r

from market_data import MarketData

class OpenStockPosition:
    """Class used for real trading."""
    def __init__(self, ticker, budget):
        # open the position given the allocated budget
        resp = r.orders.order_buy_fractional_by_price(ticker, budget, timeInForce='gfd', extendedHours=False, jsonify=True)
        print("ORDER RESPONSE DICT: ", resp)
        # self.quantity = resp["quantity"]
        # self.open_price = resp["price"]
        self.ticker = ticker
        self.quantity = resp["quantity"]
        self.open_price = resp["price"]

    def close(self):
        pass # TODO
    

class OpenPaperPosition:
    """Class used for paper trading."""
    def __init__(self, ticker, budget, market_data):
        # open the position given the allocated budget
        # instead of buying here, just get current price and assume that's what we bought at
        self.open_price = market_data.get_data_for_ticker(ticker) # TODO get value/price etc
        self.market_data = market_data
        self.ticker = ticker
        self.quantity = budget/self.open_price

    def close(self):
        # get price right now to see what we would've sold at
        pass # TODO