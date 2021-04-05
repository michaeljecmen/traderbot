import time

import robin_stocks.robinhood as r

from singletons.market_data import MarketData
from utilities import print_with_lock
from traderbot_exception import TraderbotException

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
    # time out in 10s if order not filled
    TIMEOUT = 10
    THRESHOLD = 0.0001
    def __init__(self, ticker, budget):
        """Blocks until the order is filled, 
        or the timeout passes (in which case the order is cancelled and retried)."""
        # open the position given the allocated budget
        resp = r.orders.order_buy_fractional_by_price(
            ticker, budget, timeInForce='gfd', extendedHours=False, jsonify=True)
        resp = self.monitor_order(resp, ticker)
        print_with_lock("OPEN", resp)
        quantity = resp['cumulative_quantity']
        open_price = resp['average_price']
        super().__init__(ticker, float(quantity), float(open_price))
        self.print_open()

    def close(self):
        """Returns the close price. Blocks until the order is filled, 
        or the timeout passes (in which case the order is cancelled and retried)."""
        resp = r.order_sell_fractional_by_quantity(
            self.ticker, self.quantity, timeInForce='gfd', priceType='bid_price', extendedHours=False, jsonify=True)
        resp = self.monitor_order(resp, self.ticker)
        print_with_lock("CLOSE", resp)
        if abs(resp['cumulative_quantity'] - self.quantity) > THRESHOLD:
            raise TraderbotException(
                "sold {} shares but wanted to sell {} shares of {}. response dict {}".format(
                    resp['cumulative_quantity'], self.quantity, self.ticker, resp))
        close_price = resp['average_price']
        self.print_close(close_price)
        return close_price
    
    def monitor_order(self, resp, ticker):
        """Monitors the order with the given ID until it is filled or TIMEOUT is exceeded, in which case the order is cancelled.
        Returns the response dictionary or throws, depending on whether or not the order succeeded or failed.
        Checks for fill status twice every second."""
        order_id = resp.get('id', None)
        if order_id is None:
            raise TraderbotException("initial order for {} failed".format(ticker))
        
        # before waiting check if we already filled it
        if resp['state'] == 'filled':
            return resp

        # then check every half second
        for _ in range(2*self.TIMEOUT):
            resp = r.orders.get_stock_order_info(order_id)
            if resp['state'] == 'filled': # TODO orders are being cancelled unexpectedly
                return resp
            if resp['state'] == 'cancelled':
                raise TraderbotException("order for {} was cancelled unexpectedly: {}".format(ticker, resp))
            time.sleep(0.5)
        # TODO if partially filled here need to tell the caller as much
        # what the actual qty and price are so they can sell accordingly
        # same for when they actually sell. maybe return remaining position
        # so it works for both
        print_with_lock("TIMING OUT BUT DEBUG IN CASE PARTIAL FILL: ", resp)
        resp = r.cancel_stock_order(order_id)
        print_with_lock("debug: response from cancelling stock order: ", resp)
        raise TraderbotException("order for {} timed out".format(ticker))

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
