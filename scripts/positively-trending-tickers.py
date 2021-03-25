#!env/bin/python3
import requests
import re
import sys
import pathlib
import json

def get_api_key():
    try:
        path_to_conf = pathlib.Path("config.json")
        with open(str(path_to_conf)) as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError:
                print("config.json file incorrectly formatted")
                sys.exit(1)
            if 'social-sentiment-key' not in data.keys():
                print("\"social-sentiment-key\" key-value pair not found in config.json")
                sys.exit(1)
            return data['social-sentiment-key']
    except:
        print("config.json file not found. be sure to run this in the traderbot/ dir, not the traderbot/scripts/ dir")
        sys.exit(1)
    
    
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
            print("your social sentiment account is being throttled for"
                " overuse of the API, OR your api key is incorrect. if throttled, try again in 24hrs")
            sys.exit(1)
        last_week_of_scores = r.json()
        yesterdays_score = int(last_week_of_scores[-1]["score"])
        if yesterdays_score > 0:
            socially_interesting_tickers.append(ticker)
    return socially_interesting_tickers


if "--help" in sys.argv or "-h" in sys.argv:
    print("usage: python3 scripts/positively-trending-tickers.py")
    sys.exit(0)

print(get_trending_socially_positive_tickers(get_api_key()))