#!env/bin/python3
"""Run this script once as you're setting up the traderbot, if you want your RH account to be MFA enabled."""
import sys

import pyotp

if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) != 2:
    print("usage: python3 scripts/mfa-setup.py <YOUR_TWO_FACTOR_AUTH_SETUP_CODE_HERE>")
    print("(take a look at the README for how to get this code)")
    sys.exit(0)

# gets current mfa code
totp = pyotp.TOTP(sys.argv[1]).now()
print("------------------------------------------------------------")
print("Your 6 digit MFA-code is (RH will prompt for this): ", totp)
print("------------------------------------------------------------")
print()

print("Additionally, include the following line in your config.json file:")
print("\"mfa-setup-code\": \"{}\"".format(sys.argv[1]))
print()

print("Robinhood may ask you to enter another MFA code. If they do, run this")
print("script again to get the new 6-digit code, as the old one will have expired.")
