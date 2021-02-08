import time
import json
import pathlib
import sys

import robin_stocks as r
import pandas as pd
import pyotp

# all filescope constants will be configured in the config.json
CONFIG_FILENAME="config.json"

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
            print("\"username\" and \"password\" must be defined in config.json")
            sys.exit(1)
        return data
    except FileNotFoundError:
        print("error: config.json file not found in current directory")
        sys.exit(1)
    except json.JSONDecodeError:
        print("error: config.json incorrectly formatted")
        sys.exit(1)

# get info and log in
config = get_json_dict()
username = config["username"]
password = config["password"]

# only use mfa login if it is enabled
mfa_code=''
if "mfa-setup-code" in config.keys():
    # gets current mfa code
    totp = pyotp.TOTP(config["mfa-setup-code"]).now()
login = r.login(username, password, mfa_code=mfa_code)

print("logged in as user {}".format(username))