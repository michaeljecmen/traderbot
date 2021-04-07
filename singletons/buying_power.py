from readerwriterlock import rwlock
import robin_stocks.robinhood as r

from utilities import print_with_lock

class BuyingPower:
    """Threadsafe class for shared access/updating of budget/buying power."""
    def __init__(self, percent_to_spend, budget=None):
        self.lock = rwlock.RWLockWrite()
        self.buying_power = 0.0
        if budget is None:
            self.buying_power = float(r.profiles.load_account_profile(info='crypto_buying_power'))
        else:
            self.buying_power = min(float(r.profiles.load_account_profile(info='crypto_buying_power')), budget)
        self.amount_per_buy = self.buying_power * percent_to_spend

    def spend_and_get_amount(self):
        """Spend the previously denoted amount (a constant percent of our 
        buying power at market open). If not enough, spend all."""
        with self.lock.gen_wlock():
            spent = min(self.buying_power, self.amount_per_buy)
            self.buying_power -= spent
        return spent

    def get_available_buying_power(self):
        with self.lock.gen_rlock():
            return self.buying_power

    def add_funds(self, amount):
        """Use this when you close a position to add back the funds earned."""
        with self.lock.gen_wlock():
            self.buying_power += amount
            print_with_lock("your account now has ${}".format(self.buying_power))
