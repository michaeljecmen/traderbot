# Robinhood Traderbot
The goal of this project is to make a semi-configurable 
bot to trade a set of user-defined stocks on a robinhood 
account. Ideally I also hook it up to a raspberry pi or
throw some visuals on a web server or something as it's
supposed to be a birthday present for a friend, and I'd 
like to actually give him something tangible instead of
an idea.

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

## Installation Process
The following tutorial assumes you have access to a linux terminal with python3 installed. Look up how to do that or talk to me in real life if you
don't know how to do that part.

<ol>
	<li>Clone this repo with <code>git clone </code></li>
    <li>
        Initialize a python virtual environment in your local repo with:
        <code>python3 -m venv env</code>, installing python3 beforehand if necessary
    </li>
    <li>
        Activate the venv by running:<code>
        source env/bin/activate</code>
        <br>
        (run <code>deactivate</code> or close and reopen the terminal if
        for some reason you want to deactivate the venv)
    </li>
    <li>
        Run <code>pip install -r requirements.txt</code>
        to install the necessary dependencies and ensure
        we're working with the same versions of packages
    </li>
    <li>
        Create a file <code>config.json</code>, copy and paste the contents from <code>example.json</code>, and fill in all fields. Note: the <code>mfa-setup-code</code> field is optional, leave it blank or remove it if you don't have multi-factor authentication enabled on your Robinhood account.<br><br>To get this code, navigate <a href="https://robinhood.com/account/settings">here</a>, then, from the <b>Security</b> tab find the dropdown for <b>Two-Factor Authentication</b>. If you already have 2FA enabled, disable and re-enable it. Select <b>Authentication App</b>, then click <b>Can't scan it?</b> at the bottom of the page, under the QR code. An alphanumeric code should appear. Copy it, put the following line in your <code>config.json</code> file: <code>"mfa-setup-code": "&lt;YOUR_CODE&gt;"</code>, then run the following command with it: <code>python3 mfa-setup.py &lt;YOUR_CODE&gt;</code>. The script will respond with the 6 digit code that RH will prompt for. Just run the script again if another code is prompted for or if the first one is rejected, as the time-cycles for these codes are pretty short. The bot will now log in using MFA, provided you updated <code>config.json</code> with the setup code as described earlier this step.
    </li>
</ol>

## Usage
TODO

## Configurations
Change these fields in the <code>config.json</code> configuration file at your own risk.

### max-trades-per-day
Increase <code>max-trades-per-day</code> at your own risk. As of the time of publication, 500/day was a good boundary for not getting your account flagged. Note
that some users of the RH trading API have noted getting their accounts flagged after HFT of ~500/day, where some users have gone upwards of 2000 and been fine.
According to one user who got their account flagged: "keep the day trade counts humanlike and maybe don't trade all day every day via crypto like I was.  I think those were the 2 things that got me noticed." Anyhow, increase this value at your own risk. Removing this key from the config file will let the bot loose -- it will trade with no cap on daily trades. I set this to default at 300 per day, and will test these theories with my own RH
account before publishing the bot.

### start-of-day and end-of-day
If your Robinhood account has access to after-hours and/or pre-market trading, go ahead and change these. Otherwise, stick to the 9:30 -> 16:00 EST normal market hours.

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
