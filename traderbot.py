import time
import json
import pathlib
import sys

import robin_stocks as r
import pandas as pd

# all filescope constants will be configured in the config.json
CONFIG_FILENAME="config.json"

def get_login_info():
    """Return the username and password from the config file."""
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

        return usr, pw
    except FileNotFoundError:
        print("error: config.json file not found in current directory")
        sys.exit(1)
    except json.JSONDecodeError:
        print("error: config.json incorrectly formatted")
        sys.exit(1)

# get info and log in
username, password = get_login_info()
login = r.login(username, password)

print("hello world!")