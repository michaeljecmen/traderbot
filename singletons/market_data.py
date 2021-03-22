import threading

import robin_stocks.robinhood as r
from readerwriterlock import rwlock
from alpaca_trade_api.stream import Stream

from utilities import print_with_lock, get_mean_stddev

class TickerData:
    """POD class that stores the data for a given ticker and fine-grained 
    locks the reading and writing of it. Data is an array of the last
    N prices of the stock."""

    def __init__(self, curr_price, n):
        """n MUST be a power of 2 >= 8 for the circular buffer to work, which is crucial
        for this class' operations to be O(1)"""
        self.lock = rwlock.RWLockWrite()
        self.prices = [curr_price]
        self.n = n
        self.mask = n-1 # 0b01111 if n is 16
        self.ind = 0


    def trade_update_callback(self, t):
        with self.lock.gen_wlock():
            if len(self.prices) == self.n:
                # circular buffer with bitmasking
                self.prices[self.ind & self.mask] = t.price
                self.ind += 1
            else:
                self.prices.append(t.price)
        

    def get_price(self):
        with self.lock.gen_rlock():
            return self.price
        
    
    def get_trend(self):
        """Return mean, stddev, and whether or not the last three trades went up in price."""
        with self.lock.gen_rlock():
            mean, stddev = get_mean_stddev(self.prices)
            first = self.ind-1
            if first < 0:
                first = self.n-1
            second = first-1
            if second < 0: 
                second = self.n-1
            third = second-1
            if third < 0:
                third = self.n-1
            
            # if all three went up from prev, good sign
            # if all three went down, bad sign
            # if inconclusive, neutral
            if self.prices[first] > self.prices[second] and self.prices[second] > self.prices[third]:
                return mean, stddev, "up"
            if self.prices[first] < self.prices[second] and self.prices[second] < self.prices[third]:
                return mean, stddev, "down"
            return mean, stddev, "none"


    def print(self):
        with self.lock.gen_rlock():
            print_with_lock("TICKERDATA: ind={}, prices={}".format(self.ind, self.prices))


class MarketData:
    """Threadsafe class that handles the concurrent reading and writing of the market data
    for the relevant tickers. Should really be a singleton."""

    def __init__(self, tickers, alpaca_key, alpaca_secret_key, n):
        # all for hashless O(1) access of our sweet sweet data
        self.tickers = tickers
        self.tickers_to_indices = {}
        for i in range(len(tickers)):
            self.tickers_to_indices[tickers[i]] = i
        self.stream = Stream(alpaca_key, alpaca_secret_key, data_feed='iex')

        initial_data = r.stocks.get_latest_price(self.tickers, priceType=None, includeExtendedHours=True)
        self.data = []
        for ticker in tickers:
            # for each ticker, we need:
            # - most recent price
            # - rwlock
            # - callback function for stream that updates most recent price
            ticker_data = TickerData(initial_data[self.tickers_to_indices[ticker]])
            self.stream.subscribe_trades(ticker_data.trade_update_callback, ticker)
            self.data.append(ticker_data)

        # only start stream when the market is open


    def start_stream(self):
        """Call this function when the market is open.
        
        Starts a daemon thread which consumes new ticker updates
        from the Alpaca stream and updates the relevant data in this object."""
        self.stream_thread = threading.Thread(target=self.stream.run, daemon=True)
        self.stream_thread.start()


    def get_data_for_ticker(self, ticker):
        # can be called by any thread
        return self.data[self.tickers_to_indices[ticker]].get_price()
        

    def get_trend_for_ticker(self, ticker):
        return self.data[self.tickers_to_indices[ticker]].get_trend()


    def print_data(self):
        """Pretty printing for the internal data of this object."""
        print_with_lock("---- MARKET DATA ----")
        for ticker, index in self.tickers_to_indices.items():
            print_with_lock("{}: {}".format(ticker, self.data[index].get_price()))
        print_with_lock("---------------------")
