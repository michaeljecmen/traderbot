import time
import json
import pathlib
import sys
from datetime import datetime, date, timedelta
from random import randrange
import threading
import re
import pprint

import requests
import pandas as pd
import pandas_market_calendars as mcal
import pyotp
import yfinance as yf
import cbpro

from trading_thread import TradingThread
from singletons.market_data import MarketData, TickerData
from singletons.market_time import MarketTime
from singletons.buying_power import BuyingPower
from singletons.trade_capper import TradeCapper
from singletons.reports import Reports
from strategies.strategy_factory import strategy_factory, enforce_strategy_dict_legal
from utilities import print_with_lock, enforce_keys_in_dict
from traderbot_exception import ConfigException

# all filescope constants will be configured in the config.json
CONFIG_FILENAME = "config.json"

# do not change these -- will be overwritten by config.json reading anyways
# only at filescope for scoping issues, should be treated as constants by all 
# functions and threads (will only be read after config reading)
KEY = ""
B64SECRET = ""
PASSPHRASE = ""
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
    upper_bound = lower_bound + timedelta(hours=0, minutes=30)

    # interval from 0 to this value in seconds is our go-range
    interval = (upper_bound - lower_bound).seconds
    start_seconds = 0
    if interval != 0:
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
    
    todays_end_time = pick_humanlike_end_time()

    todays_trade_cap = pick_humanlike_trade_cap()

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
        time_until_start_trading = start_of_day_datetime - datetime.now()
    print_with_lock("beginning trading")

def log_in_to_coinbase():
    # only use mfa login if it is enabled
    auth_client = cbpro.AuthenticatedClient(KEY, B64SECRET, PASSPHRASE)
    print_with_lock("logged in")
    return auth_client

def get_json_dict():
    """Return the json dictionary found in config.json, throwing otherwise.
    """
    try:
        path_to_conf = pathlib.Path(CONFIG_FILENAME)
        with open(str(path_to_conf)) as json_file:
            data = json.load(json_file)
        
        necessary_config_fields = [
            "username",
            "password",
            "paper-trading",
            "max-loss-percent",
            "take-profit-percent",
            "spend-percent",
            "alpaca-api-key",
            "alpaca-secret-key",
            "strategies"
        ]
        enforce_keys_in_dict(necessary_config_fields, data)

        # TODO enforce that all tickers are all real & tradeable
        return data
    except FileNotFoundError:
        raise ConfigException("error: config.json file not found in current directory")

def run_traderbot():
    """Main function for this module.
    
    Spawns a thread for each ticker that trades on that symbol
    for the duration of the day."""
    # get info from config file and log in
    global KEY, B64SECRET, PASSPHRASE, PAPER_TRADING, TRADE_LIMIT, CONFIG
    CONFIG = get_json_dict()
    KEY = CONFIG["key"]
    B64SECRET = CONFIG["b64secret"]
    PASSPHRASE = CONFIG["passphrase"]
    MAX_LOSS_PERCENT = CONFIG["max-loss-percent"]/100.0
    TAKE_PROFIT_PERCENT = CONFIG["take-profit-percent"]/100.0
    SPEND_PERCENT = CONFIG["spend-percent"]/100.0
    PAPER_TRADING = CONFIG["paper-trading"]
    TRADE_LIMIT = CONFIG.get("max-trades-per-day", None)
    BUDGET = CONFIG.get("budget", None)
    STRATEGIES_DICT = CONFIG["strategies"]
    HISTORY_SIZE = CONFIG.get("history-len", 16)
    if not ((HISTORY_SIZE & (HISTORY_SIZE-1) == 0) and HISTORY_SIZE != 0): 
        raise ConfigException("history-len must be a power of two, {} was entered".format(HISTORY_SIZE))
    TREND_SIZE = CONFIG.get("trend-len", 3)
    if TREND_SIZE > HISTORY_SIZE:
        raise ConfigException("trend-len must be less than or equal to history-len")

    zero_time = timedelta()

    login = log_in_to_coinbase()

    # get list of unique tickers and enforce legality of strategies kv in the config
    ALL_TICKERS = []
    for st in STRATEGIES_DICT:
        enforce_keys_in_dict(['strategy', 'tickers'], st)
        enforce_strategy_dict_legal(st['strategy'])
        ALL_TICKERS.extend(st['tickers'])
    ALL_TICKERS = list(set(ALL_TICKERS))

    # these variables are shared by each trading thread. they are written by this
    # main traderbot thread, and read by each trading thread individually
    market_data = MarketData(ALL_TICKERS, HISTORY_SIZE, TREND_SIZE)
    buying_power = BuyingPower(SPEND_PERCENT, BUDGET)
    trade_capper = TradeCapper(TRADE_LIMIT)
    reports = Reports()

    # spawn thread for each ticker
    threads = []
    for st in STRATEGIES_DICT:
        strategy_dict = st['strategy']
        tickers = st['tickers']
        for ticker in tickers:
            print_with_lock("initializing thread {} with strategy configuration {}".format(ticker, strategy_dict))
            strategy = strategy_factory(strategy_dict, market_data, ticker)
            if not strategy.is_relevant():
                # don't add irrelevant tickers to the threadpool.
                # long term could figure out how to remove this
                # from the market data object too # TODO pointless for crypto which should be on 24hr?
                continue
            threads.append(TradingThread(ticker, market_data, market_time, buying_power, trade_capper, strategy, reports, TAKE_PROFIT_PERCENT, MAX_LOSS_PERCENT, PAPER_TRADING))

    # busy spin until we decided to start trading
    block_until_start_trading()

    # update before we start threads to avoid mass panic
    market_data.start_stream()
    market_time.update()

    # start all threads
    for t in threads:
        t.start()

    # update the timer in the main thread
    while market_time.is_time_left_to_trade():
        market_time.update()

    # wait for all threads to finish
    for t in threads:
        t.join()
    
    # now pretty print reports
    reports.print_eod_reports()

    # tidy up after ourselves
    r.logout()
    print_with_lock("logged out user {}".format(USERNAME))

if __name__ == "__main__":
    run_traderbot()
    # public_client = cbpro.PublicClient()
    # auth_client = cbpro.AuthenticatedClient(key, b64secret, passphrase)
    # print(auth_client.auth.__dict__)
    # accounts = auth_client.get_accounts()
    # print(accounts)
    # auth works, nice
    # orders = public_client.get_product_order_book('BTC-USD', level=2)
    # print(orders)
    # eth_hist = public_client.get_product_historic_rates('ETH-USD')
    # print(eth_hist)
    # eth_stats = public_client.get_product_24hr_stats('ETH-USD')
    # print(eth_stats)
