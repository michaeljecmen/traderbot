import time
import json
import pathlib
import sys
from datetime import datetime

import robin_stocks as r
import pandas as pd
import pandas_market_calendars as mcal
import pyotp

# all filescope constants will be configured in the config.json
CONFIG_FILENAME="config.json"

def get_next_market_open_time():
    """Based on the current time, gets the next time the market will be open."""
    # assume NYSE, we aren't doing crazy shit here
    nyse = mcal.get_calendar('NYSE')
    print(nyse)

def get_time_until_market_open():
    """Return the amount of time until the market reopens."""
    get_next_market_open_time()

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
START_OF_DAY = datetime.strptime(config.get("start-of-day", "09:30=EST"), "%H:%M=%Z").time()
END_OF_DAY = datetime.strptime(config.get("end-of-day", "16:00=EST"), "%H:%M=%Z").time()
TRADE_LIMIT = config.get("max-trades-per-day", None)

# only use mfa login if it is enabled
mfa_code=None
if "mfa-setup-code" in config.keys():
    # gets current mfa code
    totp = pyotp.TOTP(config["mfa-setup-code"]).now()
    print("DEBUG: current mfa code:", totp)
login = r.login(USERNAME, PASSWORD, mfa_code=mfa_code)
print("logged in as user {}".format(USERNAME))

# busy-spin until market open
print("current time:", datetime.now().strftime("%H:%M:%S"))
get_time_until_market_open()

#TODO: make trades until market closes


# general idea: 
#   market buy when short moving avg crosses up the long moving avg
#   per-thread: market sell when profit of 1% or loss of 1%
#   spawn thread for each open position that handles the opening and closing


# tidy up after ourselves
r.logout()
print("logged out user {}".format(USERNAME))