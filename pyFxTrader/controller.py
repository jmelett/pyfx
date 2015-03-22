# -*- coding: utf-8 -*-

import json
import time

from logbook import Logger
from etc import settings
from broker import Broker
from lib.oandapy import oandapy

log = Logger('pyFxTrader')


class TradeController(object):
    DEFAULT_STRATEGY = settings.DEFAULT_STRATEGY

    strategies = None
    broker = None
    access_token = None
    environment = None
    mode = None
    input_file = None
    instruments = []


    def __init__(self, mode=None, instruments=None):
        self.environment = settings.DEFAULT_ENVIRONMENT
        self.access_token = settings.ACCESS_TOKEN
        self.account_id = settings.ACCOUNT_ID
        self.mode = mode

        # Make sure no empty instruments are in our list
        self.instruments = [x for x in instruments.split(',') if x]


    def start(self):
        self.strategies = strategies = {}
        log.info('Starting TradeController')

        oanda_api = oandapy.API(environment=self.environment,
                                access_token=self.access_token)
        self.broker = broker = Broker(mode=self.mode, api=oanda_api)

        # Initialize the strategy for all currency pairs
        for currency_pair in self.instruments:
            if not currency_pair in strategies:
                strategies[currency_pair] = self.DEFAULT_STRATEGY(
                    instrument=currency_pair, broker=broker)
                log.info('Loading strategy for: %s' % currency_pair)
                strategies[currency_pair].start()
            else:
                raise ValueError('Please make sure that instruments are used '
                                 'only once (%s)' % currency_pair)

        if self.mode == 'backtest':
            self.start_backtest()
        elif self.mode == 'live':
            self.start_live()
        else:
            raise NotImplementedError()

    def start_backtest(self):
        ret = self.broker.init_backtest_data(self.strategies)
        if ret:
            while ret:
                for s in self.strategies:
                    self.strategies[s].recalc()

    def start_live(self):
        while True:
            for s in self.strategies:
                self.strategies[s].recalc()
            time.sleep(30)

    def red_alert(self, message=None):
        """
        Emergency function:
        - Close all open positions (TBD)
        - Inform user via E-Mail/SMS/Push
        - Halt system
        - Memory dump (TBD)
        """
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()
