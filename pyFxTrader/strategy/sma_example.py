# -*- coding: utf-8 -*-

import json
from logbook import Logger

import numpy
from . import Strategy

log = Logger('pyFxTrader')


class SmaStrategy(Strategy):
    STRATEGY_NAME = 'SmaCrossingStrategy'
    TIMEFRAMES = ['M5', 'M15']

    data_buffer = {}


    def _convert_data(self, feed):
        if not feed:
            return {}

        closeAskArray = []
        closeBidArray = []
        volumeArray = []

        for item in feed:
            closeAskArray.append(item['closeAsk'])
            closeBidArray.append(item['closeBid'])
            volumeArray.append(float(item['volume']))

        closeAskArray = numpy.asarray(closeAskArray)
        closeBidArray = numpy.asarray(closeBidArray)
        volumeArray = numpy.asarray(volumeArray)

        ret_dic = {}
        ret_dic["ask"] = closeAskArray
        ret_dic["bid"] = closeBidArray
        ret_dic["volume"] = volumeArray
        return ret_dic

    def start(self):
        pass

    def calculate(self):
        has_new_data = self.update_buffer()
        if has_new_data:
            pass  # (re)calculate open/exit signals
        return has_new_data




