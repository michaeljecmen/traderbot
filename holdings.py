from readerwriterlock import rwlock
import robin_stocks.robinhood as r

class Holdings:
    """Threadsafe class for managing holdings across multiple trading threads
    and a single master updater thread."""

    def __init__(self):
        self.lock = rwlock.RWLockWrite()
        self.holdings = {}
        self.update()
    
    def update(self):
        with self.lock.gen_wlock():
            self.holdings = r.account.build_holdings(with_dividends=False)
        
    def get_current_position_for_ticker(self, ticker):
        """Returns None if no open position for the ticker."""
        with self.lock.gen_rlock():
            return self.holdings.get(ticker, None)