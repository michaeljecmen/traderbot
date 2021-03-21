"""Class module that uses socialsentiment.io to determine which stocks to possibly buy
on a given day. """

import requests
import re

import strategies.strategy
from utilities import print_with_lock

def get_socially_trending_tickers():
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

class SocialSentiment(Strategy): # TODO because strategies are per-thread, make this just for one ticker
    def __init__(self, ticker, api_key):
        super().__init__()
        # assume that ticker is a trending stock, trust that it came from 

        # 25 api requests per day with basic account
        BASE_URL = 'https://socialsentiment.io/api/v1/'
        headers = {
            "Authorization" : "Token {}".format(api_key)
        }
        r = requests.get(url=BASE_URL+'stocks/{}/sentiment/daily/'.format(ticker), headers=headers)
        self.last_week_of_scores = r.json()

    
    def should_buy_on_tick(self):
        # TODO rely on general uptrend here, we already know it's trending
        
        pass
