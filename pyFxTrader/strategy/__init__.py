# -*- coding: utf-8 -*-

class Strategy(object):
    TIMEFRAMES = []  # e.g. ['M30', 'H2']

    def __init__(self, instrument):
        self.instrument = instrument
        if not self.TIMEFRAMES:
            raise ValueError('Please define TIMEFRAMES variable.')

    def start(self):
        """Called on strategy start."""
        raise NotImplementedError()

    def new_bar(self, instrument, cur_index):
        """Called on every bar of every instrument that client is subscribed on."""
        raise NotImplementedError()

    def execute(self, engine, instruments, cur_index):
        """Called on after all indicators have been updated for this bar's index"""
        raise NotImplementedError()

    def end(self, engine):
        """Called on strategy stop."""
        raise NotImplementedError()
