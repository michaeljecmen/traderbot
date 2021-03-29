#!env/bin/python3
"""Run this script once as you're setting up the traderbot, if you want your RH account to be MFA enabled."""
import sys
import json

import pyotp

def help():
    print("usage: ./scripts/mfa-setup.py <YOUR_TWO_FACTOR_AUTH_SETUP_CODE_HERE>")
    print("(take a look at the README for how to get this code)")
    print("alternatively, you can put the following line in your config.json file:")
    print("\"mfa-setup-code\": \"{}\"".format("<YOUR_TWO_FACTOR_AUTH_SETUP_CODE_HERE>"))
    print("and run this script as ./scripts/mfa-setup.py to get the current code")
    sys.exit(0)

def print_code(code):
    print("------------------------------------------------------------")
    print("Your 6 digit MFA-code is (RH will prompt for this): ", code)
    print("------------------------------------------------------------")
    print()

if "--help" in sys.argv or "-h" in sys.argv:
    help()

# try to get the code from the config file
try:
    with open("config.json", 'r') as conf:
        data = json.load(conf)
        setup = data['mfa-setup-code']
        totp = pyotp.TOTP(setup).now()
        print_code(totp)
        sys.exit(0)
except:
    print("tried to parse config.json and failed, using command line arg instead")

# at this point there's no config.json file, must be an actual setup job
if len(sys.argv) != 2:
    help()

# gets current mfa code
totp = pyotp.TOTP(sys.argv[1]).now()
print_code(totp)

print("Additionally, include the following line in your config.json file:")
print("\"mfa-setup-code\": \"{}\"".format(sys.argv[1]))
print()

print("Robinhood may ask you to enter another MFA code. If they do, run this")
print("script again to get the new 6-digit code, as the old one will have expired.")
