# Robinhood Traderbot
The goal of this project is to make a <b>free</b>, highly-configurable 
bot to trade a set of user-defined stocks on a robinhood 
account. Ideally I also hook it up to a raspberry pi or
throw some visuals on a web server or something as it's
supposed to be a birthday present for a friend, and I'd 
like to actually give him something tangible instead of
some software or a python package.

You should be able to throw like 50$ in there, select
a set of stocks for the bot to trade from, and watch the
thing slowly make (fingers crossed) money. 

Never done anything like this, and expecting to have some
fun regardless of the bot's success -- in that regard I am 
not expecting too much.

Why Robinhood? Well, they offer fractional trading, which is pretty necessary
if you don't have a lot of money and want to do rapid trading.
And, of course, zero commission fees. This is not an endorsement of Robinhood,
which is objectively a shitty company.

Since I first broke ground on this project Alpaca and TD Ameritrade have also started offering fractional trading via their APIs, so if there's desire for that or I get bored I could port this to either of those platforms.

## First Time?
Head down to [Other Setup](#other-setup) and downgrade your Robinhood account to use Robinhood Cash. This takes the longest out of any section on the tutorial as it
relies on RH actually doing something on their end, which can take several business days. Once you've started that process, go ahead and start the installation.

## Installation Process
The following tutorial assumes you have access to a linux terminal with python3 installed. Look up how to do that or talk to me in real life if you
don't know how to do that part.

<ol>
	<li>Clone this repo with 

```
git clone git@github.com:michaeljecmen/traderbot.git
```

</li>
<li>
    Initialize a python virtual environment in your local repo with:

```
python3 -m venv env
```

... installing python3 beforehand if necessary.
</li>
<li>
Activate the venv by running:
        
```
source env/bin/activate
```

(run <code>deactivate</code> or close and reopen the terminal if
for some reason you want to deactivate the venv)
</li>
<li>
    Run 

```
pip install -r requirements.txt
```
to install the necessary dependencies and ensure
we're working with the same versions of packages.
</li>
<li>
    Create a file <code>config.json</code>, copy and paste the contents from <code>example.json</code>, and fill in all fields. Note: the <code>mfa-setup-code</code> field is optional, leave it blank or remove it if you don't have multi-factor authentication enabled on your Robinhood account.<br><br>To get this code, navigate <a href="https://robinhood.com/account/settings">here</a>, then, from the <b>Security</b> tab find the dropdown for <b>Two-Factor Authentication</b>. If you already have 2FA enabled, disable and re-enable it. Select <b>Authentication App</b>, then click <b>Can't scan it?</b> at the bottom of the page, under the QR code. An alphanumeric code should appear. Copy it, put the following line in your <code>config.json</code> file:

```json
"mfa-setup-code": "<YOUR_CODE>"
```

then run the following command with it:

```python
python3 scripts/mfa-setup.py <YOUR_CODE>
```

The script will respond with the 6 digit code that RH will prompt for. Just run the script again if another code is prompted for or if the first one is rejected, as the time-cycles for these codes are pretty short. The bot will now log in using MFA, provided you updated <code>config.json</code> with the setup code as described earlier this step.
    </li>
    <li>
        Put the following lines in env/lib/alpaca_trade_api/stream.py in the outermost run() function: Replace

```python
loop = asyncio.get_event_loop()
```

with
    
```python
try:
    loop = asyncio.get_event_loop()
except:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
```

</li>
</ol>

## Other Setup
If you have a Robinhood Instant account (which is your account setting by default on RH), you'll need to transition it to an Robinhood Cash account, which can 
take a few business days. This is necessary because anyone trading on margin (which includes <i>all</i> RH Instant users, regardless of whether or not you actually trade on margin) is subject to FINRA's Pattern Day Trader rules. You'll be flagged as a PDT and banned from trading for 90 days if you make more than 4 day trades (where a day trade is a buy and sell of the same symbol in the same day) in 5 consecutive days. This is unrelated to RH, just an actual legal rule.

<b>That said</b>, you can get around this and continue using a Robinhood Instant account if you have $25,000 cash in your account at the end of each trading day.
This needs to be all cash, you can't have some margin, whatever that means. If you are sure this applies to you, you can skip this setup step.

Anyhow, in order to downgrade from an Instant account to a Cash account, you just need to send them an email at <code>support@robinhood.com</code> with the following information:
<ul>
<li>Confirmation that you have $0.00 in unsettled funds and no pending transactions. You can view your unsettled funds in the Account->Withdrawable Cash section and your pending transactions in the History section of the account menu. If you're on mobile, go to Account->Transfers->Withdrawable Cash->Learn More. You should see $0 in unsettled funds before you proceed. This usually takes a few business days if you've recently made a trade, so lie low for a few and let that number drop to zero.</li>
<li>Your feedback on why you no longer want to use Robinhood Instant.</li>
<li>Your understanding that you might not be able to re-upgrade to Robinhood Instant at a later date.</li>
</ul>

If you're sold on all of this, go ahead and send the email. Here's what I sent, if you need a template:

```
Hello,

I'd like to transition my account from Robinhood Instant to Robinhood Cash, please.

I'm currently have no unsettled funds and no pending transactions, I'd like to change to day trade with my cash more regularly, and I understand I may not be able to re-upgrade my account in the future.

Thanks!
Michael
```

Wait for your account to be officially downgraded, and you're set to run the bot!

## Usage
TODO talk about configuring the strategy

## Other Configurations
Change these fields in the <code>config.json</code> configuration file at your own risk.
TODO which other fields are necessary, which will be defaulted safely

### max-trades-per-day
Increase <code>max-trades-per-day</code> at your own risk. As of the time of publication, 500/day was a good boundary for not getting your account flagged. Note
that some users of the RH trading API have noted getting their accounts flagged after HFT of ~500/day, where some users have gone upwards of 2000 and been fine.
According to one user who got their account flagged: "keep the day trade counts humanlike and maybe don't trade all day every day via crypto like I was.  I think those were the 2 things that got me noticed." Anyhow, increase this value at your own risk. Removing this key from the config file will let the bot loose -- it will trade with no cap on daily trades. I set this to default at 300 per day, and will test these theories with my own RH
account before publishing the bot.

### start-of-day and end-of-day
If your Robinhood account has access to after-hours and/or pre-market trading, go ahead and change these. Otherwise, stick to the 9:30 -> 16:00 EST normal market hours. Cash accounts DO have access to these special hours, so if you have a Cash account rather than an Instant account (see [Other Setup](#other-setup)) you can
change these to the normal 9:00-17:00.

## Dependencies
Feel free to upgrade the version on the robin-stocks package in <code>requirements.txt</code>, if you're certain the api has not 
significantly changed in a way that would damage the algorithm. The key==value pair is by default <code>robin-stocks==1.7.1</code>.
<br>
Upgrade any of the dependencies if you know what you're doing.

## Further Documentation
This script uses robin-stocks, with documentation <a href="http://www.robin-stocks.com/en/latest/functions.html">here</a>. Feel free to change the algorithm to your liking or fork the repo if you've got better ideas.

The algorithm I've written is pretty rudimentary, at the end of the day,
and all of what I know with regards to trading algs I learned online over the course of a week or so.

## TODOs
https://www.activestate.com/blog/how-to-build-an-algorithmic-trading-bot/
https://pypi.org/project/robin-stocks/
^ put the step for this one in the usage and installation process part too
add support for a log file instead of console output, then email that file to the user every so often
- email support for real time issues
- hardware? run on little raspberry pi or something
- flash green when profit? good jingle vs bad jingle?
rerun the main script every 24hr

consider switching to TDA with robin_stocks 2.0.0 if accounts get flagged,
TDA has a public api and is more lenient I believe

consider switching to alpaca -- they now support fractional trading and have 
a much more algorithmic-friendly api

change back to alpaca_trade_api==1.0.1 if you have problems with asyncio event loop again
otherwise download new package version and run it

test double down on tickers in diff strategies

trade crypto -- 24/7 always opps for moneymaking
polygon does not limit api usage with pro plan, for crypto that's 50$ a month which is a great price
alpaca does not either, trade crypto on alpaca is future move

problems:
cannot trade with value of previous closed trades until 2 days after the position was closed. this is
pretty universal, and not broker/platform specific. this is only the case for cash accounts, however,
and margin accounts (provided you have over 25k of assets in the acct at each day end) are free to trade
with the value of closed positions instantly.

crypto does not have these rules!

TODO
try RH crypto, see if the rh limiting can be figured out, then jump ship to alpaca if neither consistent
either way need instant accounts back so alpaca is the move anyways
add limit order spreads to crypto, limit order at open+1% and stop loss at open-1%

jesus christ:
Market orders on Robinhood are placed as limit orders at 1% above the market price in order to protect customers from overdraft.

coinbase websocketclient class with overridden methods to mimick alpaca price streaming
nice

order placing similar enough

TODO just port the above two things on the current branch