# -*- coding: utf-8 -*-

from . import Strategy


class SmaStrategy(Strategy):
    STRATEGY_NAME = 'SmaCrossingStrategy'
    TIMEFRAMES = ['H1', 'H2']

    def start(self):
        pass
