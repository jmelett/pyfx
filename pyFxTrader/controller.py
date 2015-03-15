# -*- coding: utf-8 -*-

import json
import time

from etc import settings
from broker import Broker
from datafeed import DataFeed
from strategy.sma_example import SmaStrategy


class TradeController:
    # Change this to your flavour
    DEFAULT_STRATEGY = SmaStrategy

    _strategies = {}

    access_token = None
    environment = None
    mode = None
    input_file = None
    instruments = []


    def __init__(self, mode=None, input_file=None, instruments=None):
        self.environment = settings.DEFAULT_ENVIRONMENT
        self.access_token = settings.ACCESS_TOKEN
        self.instruments = instruments
        self.mode = mode


    def start(self, instruments):
        self._strategies = strategies = {}

        # Initialize the strategy for all currency pairs
        # TODO Implement multi-instrument/strategy functionality
        for currency_pair in self.instruments:
            if not currency_pair in strategies:
                # Create datafeed(s)
                feed_list = []
                for tf in self.DEFAULT_STRATEGY.TIMEFRAMES:
                    feed = DataFeed(timeframe=tf, mode=self.mode)
                    feed_list.append(feed)

                # And then the strategy object
                strategies[currency_pair] = self.DEFAULT_STRATEGY(
                    instrument=currency_pair,
                    feeds=feed_list
                )
                print "[+] Loading strategy for: %s" % currency_pair
                strategies[currency_pair].start()
            else:
                raise ValueError('Please make sure that instruments are used '
                                 'only once (%s)' % currency_pair)

            # Now iterate every 15 seconds through all strategy objects and
            # check if a new tick arrived; if yes, recalculate
            broker = Broker(mode=self.mode)
            while True:
                # TODO
                # 1. Check account balance, make sure nothing changed
                #    dramatically, else red_alert()!
                # 2. Check all strategy objects for a buy/sell signal
                # 3. Calculate position size and place order)
                # 4. Check if order was placed and/or others were cancelled
                # (for whatever reason)
                # 5. Send E-Mail or SMS to user in case of action required
                print broker.get_account_balance()
                for s in strategies:
                    print s
                time.sleep(15)


    def _start_backtest(self, instruments, input_file):
        raise NotImplementedError()
        # print "[+] Starting backtest for: '%s'" % instruments
        # if not self.api:
        # self.api = OandaAPI(environment=self.environment,
        # access_token=self.access_token)
        #
        # with open("data/EURUSD_M5_oanda.json") as json_m5_file:
        # json_data_m5 = json.load(json_m5_file)
        #
        # with open("data/EURUSD_M15_oanda.json") as json_m15_file:
        # json_data_m15 = json.load(json_m15_file)
        #
        # trader = Trader(json_data_m5, json_data_m15, instruments)
        # print self.api.get_account(settings.ACCOUNT_ID)

        # data1 = self.api.get_history(instrument=instrument, count=5000, granularity="M5")
        # data2 = self.api.get_history(instrument=instrument, count=5000, granularity="M15")
        # with open('EURUSD_M5_oanda.json', 'w') as outfile:
        # json.dump(data1, outfile)
        # with open('EURUSD_M15_oanda.json', 'w') as outfile:
        # json.dump(data2, outfile)

        # for x in data['candles']:
        # print "woot", x
        # check if file exists
        # for line in file call on_success
        # updated output (e.g. using curses) after each call

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
        # TODO Since feeds are attached to a strategy object, the disconnect
        # should happen via that object, e.g. strategies['EURCHF'].disconnect()
        # for strat in self._strategies:
        #     strat.disconnect()