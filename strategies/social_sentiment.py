"""Class module that uses socialsentiment.io to determine which stocks to possibly buy
on a given day. """

import requests
import re
import threading

from strategies.strategy import Strategy
from strategies.basic_trend_follower import BasicTrendFollower
from utilities import print_with_lock

def get_socially_trending_tickers():
    """Returns a list of the 10 most socially trending tickers."""
    # steal trending stocks from home page without paying for premium subscription
    # just regex the html lol
    r = requests.get(url='https://socialsentiment.io/stocks/')
    content = str(r.content)

    # may need to update this if the homepage is maintained regularly.
    # i figure the links are pretty safe, each stock has a link to its 
    # personal page of the form href="/stocks/symbol/<ticker>/" which
    # shouldn't change very often
    trending = re.findall('/stocks/symbol/[A-Z]*/', content)
    trending = [ url.split("/")[-2] for url in trending ]
    trending = list(set(trending))
    print_with_lock("today's socially trending stocks:", trending)
    return trending


class SocialSentiment(Strategy):
    market_data = {}
    ctor_lock = threading.Lock()
    def __init__(self, ticker, api_key, market_data):
        super().__init__()
        # assume that ticker is a trending stock, trust that it came from the above function
        with self.ctor_lock:
            SocialSentiment.market_data = market_data
        
        # 25 api requests per day with basic account
        BASE_URL = 'https://socialsentiment.io/api/v1/'
        headers = {
            "Authorization" : "Token {}".format(api_key)
        }
        r = requests.get(url=BASE_URL+'stocks/{}/sentiment/daily/'.format(ticker), headers=headers)
        self.last_week_of_scores = r.json()
        self.trend_follower = BasicTrendFollower(market_data, ticker, 1)

    
    def should_buy_on_tick(self):
        return self.trend_follower.should_buy_on_tick()
