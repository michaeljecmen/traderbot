import time
import json
import pathlib
import sys
from datetime import datetime, date, timedelta
from random import randrange

import robin_stocks.robinhood as r
import pandas as pd
import pandas_market_calendars as mcal
import pyotp
from yahoo_finance import Share

# all filescope constants will be configured in the config.json
CONFIG_FILENAME="config.json"

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
    # pick start time within an hour of market close
    # need dummy year month day here
    upper_bound = datetime(1,1,1, END_OF_DAY.hour, END_OF_DAY.minute, END_OF_DAY.second)
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
    print("param: will start trading today at:", todays_start_time)
    
    todays_end_time = pick_humanlike_end_time()
    print("param: will stop trading today at:", todays_end_time)

    todays_trade_cap = pick_humanlike_trade_cap()
    print("param: will make a maximum of {} trades today".format(todays_trade_cap))
    return todays_start_time, todays_end_time, todays_trade_cap


def get_next_market_open_time():
    """Based on the current time, gets the next time the market will be open.
    
    Returns a pandas.Timestamp object."""
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
    now = datetime.utcnow()
    time_until_open = next_open - now
    return time_until_open
    

def block_until_market_open():
    time_until_open = get_time_until_market_open()
    zero_time = timedelta()
    print("begin waiting until market open. time remaining:", time_until_open)
    last_print = time_until_open
    while time_until_open > zero_time:
        # TODO ensure this works when the market is actually open
        if last_print - time_until_open > timedelta(hours=1):
            print("still waiting until market open. time remaining:", time_until_open)
            last_print = time_until_open
        # update timedelta
        time_until_open = get_time_until_market_open()


def log_in_to_robinhood():
    # only use mfa login if it is enabled
    mfa_code=None
    if "mfa-setup-code" in config.keys():
        # gets current mfa code
        totp = pyotp.TOTP(config["mfa-setup-code"]).now()
        print("DEBUG: current mfa code:", totp)
    login = r.login(USERNAME, PASSWORD, mfa_code=mfa_code)
    print("logged in as user {}".format(USERNAME))
    return login

def get_json_dict():
    """Return the json dictionary found in config.json, throwing otherwise.
    
    The following fields are required (and mandated by this function):
        username
        password
    """
    try:
        path_to_conf = pathlib.Path(CONFIG_FILENAME)
        data = {}
        with open(str(path_to_conf)) as json_file:
            data = json.load(json_file)
        usr = data.get("username", "_")
        pw = data.get("password", "_")
        if usr == "_" or pw == "_":
            print("\"username\" and \"password\" must be defined in config.json -- see example.json for how to do this")
            sys.exit(1)
        return data
    except FileNotFoundError:
        print("error: config.json file not found in current directory")
        sys.exit(1)
    except json.JSONDecodeError:
        print("error: config.json incorrectly formatted")
        sys.exit(1)


# get info from config file and log in
config = get_json_dict()
USERNAME = config["username"]
PASSWORD = config["password"]
TIME_ZONE = config.get("time-zone-pandas-market-calendars", "America/New_York")
full_start_time_str = config.get("start-of-day", "09:30") + "={}".format(TIME_ZONE)
full_end_time_str = config.get("end-of-day", "16:00") + "={}".format(TIME_ZONE)
START_OF_DAY = datetime.strptime(full_start_time_str, "%H:%M=%Z").time()
END_OF_DAY = datetime.strptime(full_end_time_str, "%H:%M=%Z").time()
TRADE_LIMIT = config.get("max-trades-per-day", None)
HAVE_GENERATED_HUMANLIKE_PARAMETERS = False

login = log_in_to_robinhood()

# generate parameters so we don't get flagged
START_OF_DAY, END_OF_DAY, TRADE_LIMIT = generate_humanlike_parameters()

# busy-spin until market open
block_until_market_open()

#TODO: make trades until market closes

# general idea: 
#   market buy when short moving avg crosses up the long moving avg
#   per-thread: market sell when profit of 1% or loss of 1%
#   spawn thread for each open position that handles the opening and closing


# tidy up after ourselves
r.logout()
print("logged out user {}".format(USERNAME))

# TODO login expires after a day, so expect that the user runs the script once 
# per day (probably best after hours) and if any login trouble handle it on your own

# each traded stock spawns a thread that manages its own state machine until just before end of day when
# ordered to close positions. states include:
# not bought in
# bought in and making > 1% (above profit thresh) -- hold and sell when peak or crosses back down thresh?
# bought in and making < 1% hold until loss of 1% or state changes
# EOD state: close out position soon, or absolute sell if close to market close (within 5 minutes, say)

# ideas for data: steal data from polygon using free trial then maintain that initial data myself

# how much per trade? come up with a confidence factor in the success of the trade and invest 
# the buying power $ I have proportionially?

# use yahoo finance or pandas data -- free and dope
# https://github.com/SaltyDalty0/Finances/blob/main/quick_stonks.py
# https://pypi.org/project/yahoo-finance/