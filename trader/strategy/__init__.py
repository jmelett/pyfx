from logbook import Logger

log = Logger('pyFxTrader')


class StrategyBase(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self._is_open = False

    def open(self, order_id):
        self._is_open = True
        self._order_id = order_id

    def close(self):
        self._is_open = False

    def start(self, broker, tick):
        self.broker = broker

    def tick(self, tick):
        raise NotImplementedError()
