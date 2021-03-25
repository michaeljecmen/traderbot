"""Factory module that creates a strategy based on the dict passed from the config"""

from traderbot_exception import ConfigException
from strategies.strict_momemtum import StrictMomentum
from strategies.long_vs_short_moving_average import LongShortMovingAverage
from strategies.mean_reversion import MeanReversion
from utilities import enforce_keys_in_dict

# update this whenever you add a new strategy. used for error checking
# as early as possible.
_strategy_required_fields = {
    "LongShortMovingAverage": [
        "long", 
        "short"
    ],
    "StrictMomentum": [
        "percent"
    ],
    "MeanReversion": [
        "percent"
    ],
}

def _enforce_name_defined(strategy):
    name = strategy.get('name', "_")
    if name == "_":
        raise ConfigException("your strategy dictionary must define a \"name\""
            "key, instead dictionary was {}".format(strategy))

def strategy_factory(strategy, market_data, ticker):
    # basically just a big switch statement, you know how factories are
    enforce_strategy_dict_legal(strategy)
    name = strategy['name']

    if name == "LongShortMovingAverage":
        return LongShortMovingAverage(market_data, ticker, strategy['short'], strategy['long'])
    elif name == "StrictMomentum":
        return StrictMomentum(market_data, ticker, strategy['percent'])
    elif name == "MeanReversion":
        return MeanReversion(market_data, ticker, strategy['percent'])
    else:
        raise ConfigException("{} does not name a strategy. see the readme"
            "for a list of valid strategy names".format(name))


def enforce_strategy_dict_legal(strategy):
    """Enforces that a strategy dict is legal. Called before the big blocking calls prior to
    market open to error out as early as possible."""
    _enforce_name_defined(strategy)
    enforce_keys_in_dict(_strategy_required_fields[strategy['name']], strategy)
    