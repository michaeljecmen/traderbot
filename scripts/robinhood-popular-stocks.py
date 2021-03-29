#!env/bin/python3
"""Returns the top 100, top 20 movers (any direction), and top 'upward' movers from the s&p 500"""

import sys
import pathlib
import json
import pyotp
import pprint

import robin_stocks.robinhood as r

if "--help" in sys.argv or "-h" in sys.argv:
    print("usage: ./scripts/robinhood-popular-stocks.py")
    sys.exit(0)

# get data
try:
    path_to_conf = pathlib.Path("config.json")
    with open(str(path_to_conf)) as json_file:
        try:
            data = json.load(json_file)
        except json.JSONDecodeError:
            print("config.json file malformed -- see the following")
            raise 
except:
    print("config.json file not found. make sure you're running this script from the traderbot/ dir, not the traderbot/scripts/ dir")
    sys.exit(1)

if 'username' not in data.keys() or 'password' not in data.keys():
    print("\"username\" and \"password\" must have key-value pairs in config.json")
    sys.exit(1)

username = data['username']
password = data['password']

# log in
mfa_code=None
if 'mfa-setup-code' in data.keys():
    # gets current mfa code
    totp = pyotp.TOTP(data["mfa-setup-code"]).now()
    print("current mfa code (this may be requested momentarily):", totp)

print("data is being fetched...")
login = r.login(username, password, mfa_code=mfa_code)

# get and print data
pp = pprint.PrettyPrinter(indent=4)
top_100 = r.get_top_100()
top_100 = [d['symbol'] for d in top_100]
print("---------------------- TOP 100 ---------------------")
pp.pprint(top_100)
print("----------------------------------------------------")

top_movers_any = r.get_top_movers()
top_movers_any = [d['symbol'] for d in top_movers_any]
print("------------ TOP MOVERS (ANY DIRECTION) ------------")
pp.pprint(top_movers_any)
print("----------------------------------------------------")

top_upward_movers_sp500 = r.get_top_movers_sp500(direction='up')
top_upward_movers_sp500 = [d['symbol'] for d in top_upward_movers_sp500]
print("----------- TOP UPWARD MOVERS (S&P 500) ------------")
pp.pprint(top_movers_any)
print("----------------------------------------------------")
