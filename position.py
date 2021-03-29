import robin_stocks.robinhood as r

from singletons.market_data import MarketData

from utilities import print_with_lock


class Position:
    """Base class for minor data handling and shared printing functionality."""
    _precision = 4

    def __init__(self, ticker, quantity, open_price):
        self.ticker = ticker
        self.open_price = open_price
        self.quantity = quantity

    def _fnum(self, num):
        return "{:0.{}f}".format(num, self._precision)
    
    def get_quantity(self):
        return self.quantity

    def get_open_price(self):
        return self.open_price
        
    def print_open(self):
        fqty = self._fnum(self.quantity)
        fop = self._fnum(self.open_price)
        ftot = self._fnum(self.quantity*self.open_price)
        print_with_lock("opened {} position: {} shares at {} for ${}".format(
            self.ticker, fqty, fop, ftot))

    def print_close(self, close_price):
        fqty = self._fnum(self.quantity)
        ftot = self._fnum(self.quantity*close_price)
        fnet = self._fnum((close_price-self.open_price)*self.quantity)
        print_with_lock("sold {} shares of {} (total of ${}) for a net {} of {}".format(
            fqty, self.ticker, ftot, "gain" if close_price > self.open_price else "loss", fnet))


class OpenStockPosition(Position):
    """Class used for real trading."""

    def __init__(self, ticker, budget):
        """Blocks until the order is filled, 
        or the timeout passes (in which case the order is cancelled and retried)."""
        # open the position given the allocated budget
        resp = r.orders.order_buy_fractional_by_price(
            ticker, budget, timeInForce='gfd', extendedHours=False, jsonify=True)
        print_with_lock("ORDER RESPONSE DICT: ", resp)
        # self.quantity = resp["quantity"]
        # self.open_price = resp["price"] # TODO test and confirm that this works
        super().__init__(ticker, resp["quantity"], resp["price"])
        self.print_open()


    def close(self):
        """Returns the close price. Blocks until the order is filled, 
        or the timeout passes (in which case the order is cancelled and retried)."""
        # robin_stocks.robinhood.orders.order_sell_fractional_by_quantity(symbol, quantity, timeInForce='gfd', priceType='bid_price', extendedHours=False, jsonify=True)
        # then confirm that sell actually worked
        close_price = 0.0
        self.print_close(close_price)
        return close_price # TODO


class OpenPaperPosition(Position):
    """Class used for paper trading."""

    def __init__(self, ticker, budget, market_data):
        """Not using a "shared" market data ref here,
        too slow with the ctor_lock that would be needed.
        Just have each paper position control one market data ref."""
        # open the position given the allocated budget
        # instead of buying here, just get next price and assume that's what we bought at
        self.market_data = market_data
        open_price = market_data.get_next_data_for_ticker(ticker)
        ticker = ticker
        quantity = budget/open_price
        super().__init__(ticker, quantity, open_price)
        self.print_open()

    def close(self):
        """Returns the close price."""
        # get price right now to see what we would've sold at
        close_price = self.market_data.get_next_data_for_ticker(self.ticker)
        self.print_close(close_price)

        return close_price
