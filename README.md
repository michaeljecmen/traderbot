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

# Installation Process
<ol>
	<li>Clone this repo</li>
    <li>
        Initialize a python virtual environment in your local repo with:
        <code>python3 -m venv env</code>, installing python3 beforehand if necessary
    </li>
    <li>
        Activate the venv by running:<code>
        source env/bin/activate</code>
        <br>
        (run <code>deactivate</code> or close and reopen the terminal to deactivate the venv)
    </li>
    <li>
        Run <code>pip install -r requirements.txt</code>
        to install the necessary dependencies and ensure
        we're working with the same versions of packages
    </li>
    <li>
        Create a file <code>config.json</code>, copy and paste the contents from <code>example.json</code>, and fill in all fields. Note: the <code>mfa-setup-code</code> field is optional, leave it blank or remove it if you don't have multi-factor authentication enabled on your Robinhood account. <br><br>To get this code, navigate <a href="https://robinhood.com/account/settings">here</a>, then, from the <b>Security</b> tab find the dropdown for <b>Two-Factor Authentication</b>. If you already have 2FA enabled, disable and re-enable it. Select <b>Authentication App</b>, then click <b>Can't scan it?</b> at the bottom of the page, under the QR code. An alphanumeric code should appear. Copy it, put the following line in your <code>config.json</code> file: <code>"mfa-setup-code": "&lt;YOUR_CODE&gt;"</code>, then run the following command with it: <code>python3 mfa-setup.py &lt;YOUR_CODE&gt;</code>. The script will respond with the 6 digit code that RH will prompt for. Just run the script again if another code is prompted for or if the first one is rejected, as the time-cycles for these codes are pretty short. The bot will now log in using MFA, provided you updated <code>config.json</code> with the setup code as described earlier this step.
    </li>
</ol>

# Usage
TODO

# Configurations
Increase <code>max-trades-per-day</code> at your own risk. As of the time of publication, 500/day was a good boundary for not getting your account flagged. Note
that some users of the RH trading API have noted getting their accounts flagged after high frequency trading, where some users have gone upwards of 2000 and been fine.
According to one user who got their account flagged: "keep the day trade counts humanlike and maybe don't trade all day every day via crypto like I was.  I think those were the 2 things that got me noticed." Anyhow, increase this value at your own risk. Removing this key from the config file will let the bot loose -- it will trade with no cap on daily trades.

# TODOs
https://www.activestate.com/blog/how-to-build-an-algorithmic-trading-bot/
https://pypi.org/project/robin-stocks/
^ put the step for this one in the usage and installation process part too
add support for a log file instead of console output, then email that file to the user every so often
email support for real time issues
rerun the main script every 24hr