import time
import json
import pathlib
import sys
from datetime import datetime, date, timedelta
from random import randrange
import threading
import re

import requests
import robin_stocks.robinhood as r
import pandas as pd
import pandas_market_calendars as mcal
import pyotp
from alpaca_trade_api.stream import Stream
import yfinance as yf

from trading_thread import TradingThread
from singletons.market_data import MarketData
from singletons.market_time import MarketTime
from singletons.holdings import Holdings
from singletons.buying_power import BuyingPower
from singletons.trade_capper import TradeCapper
from strategies.long_vs_short_moving_average import LongShortMovingAverage
from utilities import print_with_lock

# all filescope constants will be configured in the config.json
CONFIG_FILENAME = "config.json"

# do not change these -- will be overwritten by config.json reading anyways
# only at filescope for scoping issues, should be treated as constants by all 
# functions and threads (will only be read after config reading)
USERNAME = ""
PASSWORD = ""
TICKERS = ""
PAPER_TRADING = ""
TIME_ZONE = ""
START_OF_DAY = ""
END_OF_DAY = ""
TRADE_LIMIT = ""
CONFIG = ""

# "humanlike" parameters to be chosen randomly every day
def pick_humanlike_start_time():
    # pick start time within first 30 minutes of market open
    # need dummy year month day here
    lower_bound = datetime(1,1,1, START_OF_DAY.hour, START_OF_DAY.minute, START_OF_DAY.second)
    upper_bound = lower_bound + timedelta(minutes=30)

    # interval from 0 to this value in seconds is our go-range
    interval = (upper_bound - lower_bound).seconds
    start_seconds = randrange(interval)

    start_time = lower_bound + timedelta(seconds=start_seconds)
    return start_time.time()


def pick_humanlike_end_time():
    # give ourselves a 5 minute window on the upper end, don't want to 
    # leave it too close if we need to close out positions at EOD
    minute = END_OF_DAY.minute-5
    hour = END_OF_DAY.hour
    if minute < 0:
        minute = 60 + minute
        hour = hour - 1
    
    # pick end time within an hour of market close
    # need dummy year month day here
    upper_bound = datetime(1,1,1, hour, minute, END_OF_DAY.second)
    lower_bound = upper_bound - timedelta(minutes=60)

    # interval from 0 to this value in seconds is our go-range
    interval = (upper_bound - lower_bound).seconds
    seconds_from_end = randrange(interval)

    end_time = upper_bound - timedelta(seconds=seconds_from_end)
    return end_time.time()


def pick_humanlike_trade_cap():
    # pick trade limit within 100 of trade cap
    return TRADE_LIMIT - randrange(100)


def generate_humanlike_parameters():
    # "today" means the next trading day
    todays_start_time = pick_humanlike_start_time()
    print_with_lock("param: will start trading today at:", todays_start_time)
    
    todays_end_time = pick_humanlike_end_time()
    print_with_lock("param: will stop trading today at:", todays_end_time)

    todays_trade_cap = pick_humanlike_trade_cap()
    print_with_lock("param: will make a maximum of {} trades today".format(todays_trade_cap))
    return todays_start_time, todays_end_time, todays_trade_cap


def get_next_market_open_time():
    """Based on the current time, gets the next time the market will be open.
    
    If the market is open today, returns today's market open time. Returns a pandas.Timestamp object.
    Time returned is in UTC."""
    # assume NYSE, we aren't doing crazy shit here
    nyse = mcal.get_calendar('NYSE')
    
    # market never closes for a week, get first time open in the next week
    today = date.today()
    in_one_week = today + timedelta(days=7)

    # format as YYYY-MM-DD for mcal
    # fmt = "%Y-%m-%d" # unnecessary, at least with EST
    sched = nyse.schedule(start_date=today, end_date=in_one_week)
    next_market_open = sched['market_open'][0] # keep it as UTC for most calculations
    return next_market_open.to_pydatetime().replace(tzinfo=None)


def get_time_until_market_open():
    """Return the amount of time until the market reopens."""
    next_open = get_next_market_open_time()
    # returns time in utc, so use utc as well
    now = datetime.utcnow()
    time_until_open = next_open - now
    return time_until_open
    

def block_until_market_open():
    """Block until market open.
    
    Does pre-market work as soon as the loop is entered, exactly once."""
    time_until_open = get_time_until_market_open()
    zero_time = timedelta()
    last_print = time_until_open
    while time_until_open > zero_time:
        if last_print - time_until_open > timedelta(hours=1):
            print_with_lock("still waiting until market open. time remaining:", time_until_open)
            last_print = time_until_open
        # update timedelta
        time_until_open = get_time_until_market_open()
    print_with_lock("market is open")


def block_until_start_trading():
    """Block until the pre-determined time when we will start trading.
    
    Market is open at this time, so statistics can be gathered and 
    updated in this loop."""
    now = datetime.now()
    start_of_day_datetime = datetime(now.year, now.month, now.day, START_OF_DAY.hour, START_OF_DAY.minute, START_OF_DAY.second, START_OF_DAY.microsecond)
    time_until_start_trading = start_of_day_datetime - now
    zero_time = timedelta()
    last_print = time_until_start_trading
    while time_until_start_trading > zero_time:
        if last_print - time_until_start_trading > timedelta(minutes=5):
            print_with_lock("market is open. will start trading in: ", time_until_start_trading)
            last_print = time_until_start_trading
        time_until_start_trading = start_of_day_datetime - now
    print_with_lock("beginning trading")


def log_in_to_robinhood():
    # only use mfa login if it is enabled
    mfa_code=None
    if "mfa-setup-code" in CONFIG.keys():
        # gets current mfa code
        totp = pyotp.TOTP(CONFIG["mfa-setup-code"]).now()
        print_with_lock("DEBUG: current mfa code:", totp)
    login = r.login(USERNAME, PASSWORD, mfa_code=mfa_code)
    print_with_lock("logged in as user {}".format(USERNAME))
    return login


def get_json_dict():
    """Return the json dictionary found in config.json, throwing otherwise.
    
    The following fields are required (and mandated by this function):
        username
        password
        tickers
        paper-trading
    """
    try:
        path_to_conf = pathlib.Path(CONFIG_FILENAME)
        data = {}
        with open(str(path_to_conf)) as json_file:
            data = json.load(json_file)
        usr = data.get("username", "_")
        pw = data.get("password", "_")
        tickers = data.get("tickers", "_")
        pt = data.get("paper-trading", "_")
        max_loss = data.get("max-loss-percent", "_")
        take_profit = data.get("take-profit-percent", "_") # TODO in the future allow this to be per-ticker
        spend_percent = data.get("spend-percent", "_")
        alpaca_key = data.get("alpaca-api-key", "_")
        alpaca_secret_key = data.get("alpaca-secret-key", "_")
        if usr == "_" or pw == "_" or tickers == "_" or pt == "_" or max_loss == '_' or take_profit == '_' or spend_percent == '_' or alpaca_key == '_' or alpaca_secret_key == '_':
            print_with_lock("\"username\", \"password\", \"tickers\", \"paper-trading\", \"max-loss-percent\", "
             "\"take-profit-percent\", \"spend-percent\", \"alpaca-api-key\", and \"alpaca-secret-key\" must "
             "be defined in config.json -- see example.json for how to do this")
            sys.exit(1)
        # TODO enforce that all tickers are all real & tradeable
        return data
    except FileNotFoundError:
        print_with_lock("error: config.json file not found in current directory")
        sys.exit(1)
    except json.JSONDecodeError:
        print_with_lock("error: config.json incorrectly formatted")
        sys.exit(1)


def run_traderbot():
    """Main function for this module.
    
    Spawns a thread for each ticker that trades on that symbol
    for the duration of the day."""
    # get info from config file and log in
    global USERNAME, PASSWORD, TICKERS, PAPER_TRADING, TIME_ZONE
    global START_OF_DAY, END_OF_DAY, TRADE_LIMIT, CONFIG
    CONFIG = get_json_dict()
    USERNAME = CONFIG["username"]
    PASSWORD = CONFIG["password"]
    TICKERS = CONFIG["tickers"]
    MAX_LOSS_PERCENT = CONFIG["max-loss-percent"]
    TAKE_PROFIT_PERCENT = CONFIG["take-profit-percent"]
    SPEND_PERCENT = CONFIG["spend-percent"]
    PAPER_TRADING = CONFIG["paper-trading"]
    TIME_ZONE = CONFIG.get("time-zone-pandas-market-calendars", "America/New_York")
    full_start_time_str = CONFIG.get("start-of-day", "09:30") + "={}".format(TIME_ZONE)
    full_end_time_str = CONFIG.get("end-of-day", "16:00") + "={}".format(TIME_ZONE)
    START_OF_DAY = datetime.strptime(full_start_time_str, "%H:%M=%Z").time()
    END_OF_DAY = datetime.strptime(full_end_time_str, "%H:%M=%Z").time()
    TRADE_LIMIT = CONFIG.get("max-trades-per-day", None)
    ALPACA_KEY = CONFIG["alpaca-api-key"]
    ALPACA_SECRET_KEY = CONFIG["alpaca-secret-key"]
    zero_time = timedelta()

    login = log_in_to_robinhood()

    # generate parameters so we don't get flagged
    START_OF_DAY, END_OF_DAY, TRADE_LIMIT = generate_humanlike_parameters()

    # busy-spin until market open
    # block_until_market_open() #TODO uncomment

    # these variables are shared by each trading thread. they are written by this
    # main traderbot thread, and read by each trading thread individually
    market_data = MarketData(TICKERS, ALPACA_KEY, ALPACA_SECRET_KEY)
    holdings = Holdings()
    buying_power = BuyingPower(SPEND_PERCENT)
    trade_capper = TradeCapper(TRADE_LIMIT)

    # now that market open is today, update EOD for time checking
    now = datetime.now()
    END_OF_DAY = datetime(now.year, now.month, now.day, END_OF_DAY.hour, END_OF_DAY.minute, END_OF_DAY.second, END_OF_DAY.microsecond)
    market_time = MarketTime(END_OF_DAY)

    # spawn thread for each ticker
    threads = []
    for ticker in TICKERS:
        # using the 50 vs 200 day moving average strategy
        strategy = LongShortMovingAverage(market_data, ticker, 50, 200)
        threads.append(TradingThread(ticker, market_data, market_time, holdings, buying_power, trade_capper, strategy, TAKE_PROFIT_PERCENT, MAX_LOSS_PERCENT, PAPER_TRADING))

    # after all threads have subscribed the 
    # busy spin until we decided to start trading
    # block_until_start_trading() #TODO uncomment

    # update before we start threads to avoid mass panic
    market_data.start_stream()
    # holdings.update()
    market_time.update()

    # start all threads
    for t in threads:
        t.start()

    # consider having two separate threads update holdings and prices
    i = 0
    while market_time.is_time_left_to_trade():
        # holdings.update()
        market_time.update()
        if i % 500000 == 0: # TODO remove after debugging complete
            market_data.print_data()
        i += 1

    # wait for all threads to finish
    for t in threads:
        t.join()

    # tidy up after ourselves
    r.logout()
    print_with_lock("logged out user {}".format(USERNAME))

    # TODO login expires after a day, so expect that the user runs the script once 
    # per day (probably best after hours) and if any login trouble handle it on your own

    # each traded stock spawns a thread that manages its own state machine until just before end of day when
    # ordered to close positions. states include:
    # not bought in
    # bought in and making > 1% (above profit thresh) -- hold and sell when peak or crosses back down thresh?
    # bought in and making < 1% hold until loss of 1% or state changes
    # EOD state: close out position soon, or absolute sell if close to market close (within 5 minutes, say)

    # how much per trade? come up with a confidence factor in the success of the trade and invest 
    # the buying power $ I have proportionially?

    # use yahoo finance or pandas data -- free and dope
    # https://github.com/SaltyDalty0/Finances/blob/main/quick_stonks.py
    # https://pypi.org/project/yahoo-finance/

# TODO figure out how to backtest this all on historical data
if __name__ == "__main__":
    run_traderbot()

    ### socialsentiment test, worked well, implementing as strategy
    # 25 api requests per day with basic account
    # steal trending stocks from home page without paying for premium subscription
    # just regex the html lol
    # r = requests.get(url='https://socialsentiment.io/stocks/')
    # content = str(r.content)
    # m = re.findall('/stocks/symbol/[A-Z]*/', content)
    # m = [ url.split("/")[-2] for url in m ]
    # m = list(set(m))
    # print("today's trending stocks:", m)

    # BASE_URL = 'https://socialsentiment.io/api/v1/'
    # API_KEY = 'YOUR_API_KEY'
    # headers = {
    #     "Authorization" : "Token {}".format(API_KEY)
    # }
    # for ticker in m:
    #     r = requests.get(url=BASE_URL+'stocks/{}/sentiment/daily/'.format(ticker), headers=headers)
    #     print(r.json())

    ### alpaca test, worked well, implementing
    # stream = Stream('AKEK257SVC1NSFDCSTMF', 'uGhNF4IFJ60qAnf4ODp8DAxcr2fe50FDLG8H0qwJ', data_feed='iex')
    # async def trade_callback(t):
    #     print("trade made:", t.symbol, t.price)
    # async def amzn_callback(t):
    #     print("AMZN TRADE MADE:", t.symbol, t.price)
    # async def aapl_callback(t):
    #     print("AAPL TRADE MADE:", t.symbol, t.price)
    # async def goog_callback(t):
    #     print("GOOG TRADE MADE:", t.symbol, t.price)
    # callbacks = []
    # callbacks.append(aapl_callback)
    # callbacks.append(amzn_callback)
    # callbacks.append(goog_callback)
    # tickers = ["AAPL", "AMZN", "GOOG"]
    # for i in range(len(tickers)):
    #     stream.subscribe_trades(callbacks[i], tickers[i])
    # stream.run()
    # while True:
    #     pass

    #### yfinance test, kind of slow
    # count = 0
    # tickers = [yf.Ticker("MSFT"), yf.Ticker("AAPL"), yf.Ticker("AMZN"), yf.Ticker("GOOG"), yf.Ticker("NFLX")]
    # while True:
    #     for ticker in tickers:
    #         count += 1
    #         print("REQUEST NUMBER {}:".format(count), ticker.history(period="1m", interval="1m", prepost=True))
    
