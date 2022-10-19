class Logger(object):

    def __init__(self, debug=True, verbose=False, perf=False):
        self._debug = debug
        self._verbose = verbose
        self._perf = perf

    def log(self, message: str):
        print(message)

    def debug(self, message: str, verbose=False):
        if self._debug:
            if self._verbose ^ (not verbose):
                print(message)

    def perf(self, message: str):
        if self._perf:
            print(message)

    def is_debug(self):
        return self._debug

    def is_verbose(self):
        return self._verbose


LOGGER = Logger(perf=True)
