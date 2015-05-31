from logbook import Logger

log = Logger('pyFxTrader')


class StrategyBase(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self._is_open = False

    def open(self):
        self._is_open = True

    def start(self, broker, tick):
        self.broker = broker

    def tick(self, tick):
        raise NotImplementedError()
