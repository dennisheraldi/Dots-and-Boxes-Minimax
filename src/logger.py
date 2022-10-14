class Logger:

    _debug: bool
    _verbose: bool
    _perf: bool

    def __init__(self, debug=True, verbose=False, perf=False):
        # type: (bool, bool, bool) -> None

        self._debug = debug
        self._verbose = verbose
        self._perf = perf

    def log(self, message):
        # type: (str) -> None
        print(message)

    def debug(self, message, verbose=False):
        # type: (str) -> None
        if self._debug:
            if self._verbose ^ (not verbose):
                print(message)

    def perf(self, message):
        # type: (str) -> None
        if self._perf:
            print(message)

    def is_debug(self):
        # type: () -> None
        return self._debug

    def is_verbose(self):
        # type: () -> None
        return self._verbose

LOGGER = Logger(perf=True)