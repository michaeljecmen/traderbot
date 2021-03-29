import threading
import pprint

from utilities import print_with_lock

class Reports:
    """Threadsafe class that handles the concurrent reading and writing of the individual
    thread reports. Should really be a singleton."""
    lock = threading.Lock()
    reports = []
    def __init__(self):
        pass

    def add_eod_report(self, report):
        with self.lock:
            self.reports.append(report)
    
    def print_eod_reports(self):
        net = 0.0
        trades = 0
        pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)
        print_with_lock("=============================== EOD REPORTS ===============================")
        for report in self.reports:
            net += report['traderbot net performance']
            trades += report['total trades made']
            pp.pprint(report)
        print_with_lock("===========================================================================")
        print_with_lock("final summary: {} trades made for a net profit of {}".format(trades, net))
