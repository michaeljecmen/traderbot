import threading
import requests
import re

_print_lock = threading.Lock()

def print_with_lock(*args):
    with _print_lock:
        for arg in args:
            print(arg, end=' ')
        print()


def get_mean_stddev(arr):
    """Return mean and stddev of the given array."""
    mean = sum(arr)/len(arr)
    square_diffs = []
    for val in arr:
        square_diffs.append((val-mean)**2)
    stddev = (sum(square_diffs)/len(square_diffs))**0.5
    return mean, stddev


def get_trending_socially_positive_tickers(api_key):
    """Returns a list of tickers worth looking into
    (based on social sentiment scores over the last week).
    
    For now, just returns the list of trending stocks with positive scores today."""
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
    
    # but we don't just want the trending ones, want the trending ones with positive scores
    socially_interesting_tickers = []
    for ticker in trending:
        # 25 api requests per day with basic account
        BASE_URL = 'https://socialsentiment.io/api/v1/'
        headers = {
            "Authorization" : "Token {}".format(api_key)
        }
        r = requests.get(url=BASE_URL+'stocks/{}/sentiment/daily/'.format(ticker), headers=headers)
        if r.status_code != requests.codes.ok:
            raise requests.RequestException("your social sentiment account is being throttled for overuse of the API, try again in 24hrs")
        last_week_of_scores = r.json()
        yesterdays_score = int(last_week_of_scores[-1]["score"])
        if yesterdays_score > 0:
            socially_interesting_tickers.append(ticker)
    return socially_interesting_tickers
