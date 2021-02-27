import robin_stocks.robinhood as r
from readerwriterlock import rwlock

class MarketData:
    """Threadsafe class that handles the concurrent reading and writing of the market data
    for the relevant tickers. Should really be a singleton."""

    def __init__(self, tickers):
        self.lock = rwlock.RWLockWrite()
        self.tickers = tickers
        self.data = {}
        self.update()
    

    def update(self):
        # should only be called by the main thread
        with lock.gen_wlock():
            self.data = r.stocks.get_latest_price(tickers, priceType=None, includeExtendedHours=True)
        

    def get_data_for_ticker(self, ticker):
        # can be called by any thread
        with lock.get_rlock():
            return self.data.get(ticker)
