import robin_stocks.robinhood as r
from readerwriterlock import rwlock

class MarketData:
    """Threadsafe class that handles the concurrent reading and writing of the market data
    for the relevant tickers. Should really be a singleton."""

    def __init__(self, tickers):
        self.lock = rwlock.RWLockWrite()
        self.tickers = tickers
        self.tickers_to_indices = {}
        for i in range(len(tickers)):
            self.tickers_to_indices[tickers[i]] = i
        self.data = {}
        self.update()
    

    def update(self):
        # should only be called by the main thread
        with self.lock.gen_wlock():
            self.data = r.stocks.get_latest_price(self.tickers, priceType=None, includeExtendedHours=True)

        # for debugging purposes only
        self.print_data()
        

    def get_data_for_ticker(self, ticker):
        # can be called by any thread
        with self.lock.gen_rlock():
            return self.data[self.tickers_to_indices[ticker]]
        
    def print_data(self):
        """Pretty printing for the internal data of this object."""
        with self.lock.gen_rlock():
            print("---- MARKET DATA ----")
            for ticker, index in self.tickers_to_indices.items():
                print("{}: {}".format(ticker, self.data[index]))
            print("---------------------")

