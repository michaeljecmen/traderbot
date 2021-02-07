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

# Usage and Installation Process
<ol>
	<li>Clone this repo</li>
    <li>
        Initialize a python virtual environment in your local repo with:
            <p>python3 -m venv env</p>
    </li>
    <li>
        Activate the venv:<br>
        source env/bin/activate
        <br>
        (run <code>deactivate</code> or close and reopen the terminal to deactivate the venv)
    </li>
    <li>
        Run <code>pip install -r requirements.txt</code>
        to install the necessary dependencies and ensure
        we're working with the same versions of packages
    </li>
    <li>Create a file <code>config.json</code> and populate it with the following data:<br>
        <p>{</p>
            <p>"username":"&ltyour username&gt"</p>
            <p>"password":"&ltyour password&gt"</p>
        <p>}</p>
    </li>
</ol>

# TODOs
follow this tutorial and make it so MFA code is unneeded
https://www.activestate.com/blog/how-to-build-an-algorithmic-trading-bot/
https://pypi.org/project/robin-stocks/
^ put the step for this one in the usage and installation process part too

