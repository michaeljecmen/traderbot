import threading
import requests
import re

from traderbot_exception import APIException, ConfigException


_print_lock = threading.Lock()

def print_with_lock(*args):
    with _print_lock:
        for arg in args:
            print(arg, end=' ')
        print()


def get_mean_stddev(arr):
    """Return mean and stddev of the given array."""
    mean = sum(arr)/len(arr)
    square_diffs = []
    for val in arr:
        square_diffs.append((val-mean)**2)
    stddev = (sum(square_diffs)/len(square_diffs))**0.5
    return mean, stddev

def enforce_keys_in_dict(keys, dic):
    """Raises ConfigException if all keys are not in the provided dict."""
    for key in keys:
        if key not in dic.keys():
            raise ConfigException("key {} was not found in the config. see the readme for more details")