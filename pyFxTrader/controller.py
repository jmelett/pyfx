# -*- coding: utf-8 -*-

import time

from logbook import Logger

from etc import settings
from broker import Broker
from strategy.sma_example import SmaStrategy

log = Logger('pyFxTrader')


class TradeController(object):
    # Change this to your flavour
    DEFAULT_STRATEGY = SmaStrategy

    _strategies = {}

    access_token = None
    environment = None
    mode = None
    input_file = None
    instruments = []


    def __init__(self, mode=None, instruments=None):
        self.environment = settings.DEFAULT_ENVIRONMENT
        self.access_token = settings.ACCESS_TOKEN
        self.mode = mode
        # Make sure no empty instruments are in our list
        self.instruments = [x for x in instruments.split(',') if x]


    def start(self):
        self._strategies = strategies = {}
        log.info('Starting TradeController')
        # TODO Implement multi-instrument/strategy functionality
        # Initialize the strategy for all currency pairs
        for currency_pair in self.instruments:
            if not currency_pair in strategies:
                strategies[currency_pair] = self.DEFAULT_STRATEGY(
                    instrument=currency_pair)
                log.info('Loading strategy for: %s' % currency_pair)
                strategies[currency_pair].start()
            else:
                raise ValueError('Please make sure that instruments are used '
                                 'only once (%s)' % currency_pair)

        broker = Broker(mode=self.mode)
        while True:
            log.info(
                u'Current balance: {0:f}'.format(broker.get_account_balance()))
            # Iterate every tick through all strategy objects and
            # recalculate if required
            # TODO
            # 1. Check account balance, make sure nothing changed
            # dramatically, else red_alert()!
            # 2. Check all strategy objects for a buy/sell signal
            # 3. Calculate position size and place order)
            # 4. Check if order was placed and/or others were cancelled
            # (for whatever reason)
            # 5. Send E-Mail or SMS to user in case of action required
            for s in strategies:
                print s
            time.sleep(5)


    def _start_backtest(self, instruments, input_file):
        raise NotImplementedError()


    def _start_live(self, accountId, instruments):
        raise NotImplementedError()


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