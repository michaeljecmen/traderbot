import threading

import robin_stocks.robinhood as r
from readerwriterlock import rwlock
from alpaca_trade_api.stream import Stream

from utilities import print_with_lock

class TickerData:
    """POD class that stores the data for a given ticker and fine-grained 
    locks the reading and writing of it."""

    def __init__(self, curr_price):
        self.lock = rwlock.RWLockWrite()
        self.price = curr_price


    async def trade_update_callback(self, t):
        with self.lock.gen_wlock():
            self.price = t.price
        

    def get_price(self):
        with self.lock.gen_rlock():
            return self.price


class MarketData:
    """Threadsafe class that handles the concurrent reading and writing of the market data
    for the relevant tickers. Should really be a singleton."""

    def __init__(self, tickers, alpaca_key, alpaca_secret_key):
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
        
    
    def print_data(self):
        """Pretty printing for the internal data of this object."""
        print_with_lock("---- MARKET DATA ----")
        for ticker, index in self.tickers_to_indices.items():
            print_with_lock("{}: {}".format(ticker, self.data[index].get_price()))
        print_with_lock("---------------------")

# TODO track the last like N prices so we can track a very short term trend