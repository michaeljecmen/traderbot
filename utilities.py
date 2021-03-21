import threading

_print_lock = threading.Lock()

def print_with_lock(*args):
    with _print_lock:
        for arg in args:
            print(arg, end=' ')
        print()
