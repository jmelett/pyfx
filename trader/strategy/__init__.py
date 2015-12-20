# -*- coding: utf-8 -*-

class StrategyBase(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self.positions = []

        if self.current_tick_timeframe and not self.current_tick_timeframe in self.timeframes:
            raise Exception('Current timeframe needs to be part of timeframes list')


    def open_position(self, position):
        self.positions.append(position)
        return True

    def close_position(self, position):
        self.positions.remove(position)
        return True

    @property
    def is_open(self):
        for p in self.positions:
            if p.is_open:
                return True
        return False

    def start(self, broker, tick):
        self.broker = broker

    def tick(self, tick):
        self.last_tick = tick.isoformat()
