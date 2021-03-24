import threading

import robin_stocks.robinhood as r
from readerwriterlock import rwlock
from alpaca_trade_api.stream import Stream

from utilities import print_with_lock, get_mean_stddev

class TickerData:
    """POD class that stores the data for a given ticker and fine-grained 
    locks the reading and writing of it. Data is an array of the last
    N prices of the stock."""

    def __init__(self, curr_price, history_len, trend_len):
        """n MUST be a power of 2 >= 8 for the circular buffer to work, which is crucial
        for this class' operations to be O(1)"""
        assert(trend_len >= 2 and trend_len <= history_len) # k must be at least 2
        self.lock = rwlock.RWLockWrite()
        self.prices = [float(curr_price)]
        self.history_len = history_len
        self.trend_len = trend_len
        self.mask = history_len-1 # 0b01111 if n is 16
        self.ind = 0
        self.has_price_update_occurred = False


    async def trade_update_callback(self, t):
        with self.lock.gen_wlock():
            if len(self.prices) == self.history_len:
                # circular buffer with bitmasking
                if self.ind == self.history_len:
                    self.ind = 0
                self.prices[self.ind & self.mask] = float(t.price)
                self.ind += 1
            else:
                self.prices.append(float(t.price))
                self.ind += 1
            self.has_price_update_occurred = True
        

    def get_price(self):
        with self.lock.gen_rlock():
            return self.prices[self.ind-1]
        
    
    def get_next_price(self):
        """Blocks until the next price comes in from the callback."""
        with self.lock.gen_wlock():
            self.has_price_update_occurred = False
        
        # now block until it switches back
        # not using cvs here because we only use
        # this function for paper trading and id rather not
        # stuff up the callback function just for that
        lock = self.lock.gen_rlock()
        lock.acquire()
        while not self.has_price_update_occurred:
            lock.release()
            lock.acquire()
        
        # now return recent price
        lock.release()
        return self.get_price()


    def get_last_k_prices_in_order(self):
        """This function assumes you have the rlock already."""
        # first get the indices (will add n to the negative ones later)
        last_k_in_order = []
        i = self.ind-1
        for _ in range(self.trend_len):
            last_k_in_order.append(i)
            i -= 1

        return list(map((lambda x: self.prices[x] if x in range(len(self.prices)) else self.prices[x+len(self.prices)]), last_k_in_order))
    

    def get_trend(self):
        """Return mean, stddev, and whether or not the last K trades went up in price."""
        with self.lock.gen_rlock():
            mean, stddev = get_mean_stddev(self.prices)

            # if less than 3 prices, return none
            if len(self.prices) < self.trend_len:
                return mean, stddev, "none"
            last_k_in_order = self.get_last_k_prices_in_order()

            # if all k went up from prev, good sign
            # if all k went down, bad sign
            # if inconclusive, neutral

            # legal because k must be >= 2
            up = last_k_in_order[0] > last_k_in_order[1]
            prev = last_k_in_order[1]
            for i in range(1, len(last_k_in_order)):
                if up:
                    if last_k_in_order[i] <= prev:
                        return mean, stddev, "none"
                    prev = last_k_in_order[i]
                else:
                    if last_k_in_order[i] >= prev:
                        return mean, stddev, "none"
                    prev = last_k_in_order[i]
            
            # otherwise all k passed the trend
            return mean, stddev, "up" if up else "down"


    def print(self):
        with self.lock.gen_rlock():
            print_with_lock("TICKERDATA: ind={}, prices={}".format(self.ind, self.prices))


class MarketData:
    """Threadsafe class that handles the concurrent reading and writing of the market data
    for the relevant tickers. Should really be a singleton."""

    def __init__(self, tickers, alpaca_key, alpaca_secret_key, history_len, trend_len):
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
            ticker_data = TickerData(initial_data[self.tickers_to_indices[ticker]], history_len, trend_len)
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
    

    def get_next_data_for_ticker(self, ticker):
        return self.data[self.tickers_to_indices[ticker]].get_next_price()


    def get_trend_for_ticker(self, ticker):
        return self.data[self.tickers_to_indices[ticker]].get_trend()


    def print_data(self):
        """Pretty printing for the internal data of this object."""
        print_with_lock("---- MARKET DATA ----")
        for ticker, index in self.tickers_to_indices.items():
            ticker_data = self.data[index]
            with ticker_data.lock.gen_rlock():
                if len(ticker_data.prices) < ticker_data.k:
                    # make a reversed copy of the list
                    data_snippet = ticker_data.prices[::-1]
                else:
                    data_snippet = ticker_data.get_last_k_prices_in_order()
                
                # data will always be nonempty for a ticker
                print_with_lock("{}: {} {}".format(ticker, data_snippet[0], data_snippet))
        print_with_lock("---------------------")
