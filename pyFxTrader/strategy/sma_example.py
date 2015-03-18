# -*- coding: utf-8 -*-

import json
import time

from logbook import Logger
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from . import Strategy
from utils.indicators import moving_average, \
    moving_average_convergence as macd, relative_strength as rsi


log = Logger('pyFxTrader')

SMA_FAST = 10
SMA_SLOW = 50


class SmaStrategy(Strategy):
    STRATEGY_NAME = 'SmaCrossingStrategy'
    TIMEFRAMES = ['H1', 'H2']


    def __init__(self, *args, **kwargs):
        super(SmaStrategy, self).__init__(*args, **kwargs)
        self.data_frame = {}

    def _convert_data(self, feed, timeframe):
        if not feed:
            return None

        close_array = []
        volume_array = []
        time_array = []
        time_formatted_array = []
        for item in feed:
            close_array.append(item['closeMid'])
            volume_array.append(float(item['volume']))
            time_array.append(item['time'])
            time_formatted_array.append(item['time'][11:16])

        sma_fast_array = moving_average(close_array, SMA_FAST)
        sma_slow_array = moving_average(close_array, SMA_SLOW)
        macd_array = macd(close_array, simple=True)
        rsi_array = rsi(close_array, 14)

        close_array = np.asarray(close_array)
        volume_array = np.asarray(volume_array)

        ret_df = pd.DataFrame(index=time_array,
                              data={'time': time_formatted_array,
                                    'close': close_array,
                                    'volume': volume_array,
                                    'sma_fast': sma_fast_array,
                                    'sma_slow': sma_slow_array,
                                    'macd': macd_array,
                                    'rsi': rsi_array,
                              })

        ret_df.tail(50).plot(x='time',
                             y=['close', 'sma_fast', 'sma_slow', ])
        plt.suptitle('%s/%s (%s), %s' % (self.instrument, timeframe, self.STRATEGY_NAME, time.strftime("%c")))
        plt.savefig(u'plots/{0:s}_{1:s}'.format(self.instrument, timeframe))

        return ret_df

    def start(self):
        pass

    def recalc(self):
        has_new_data = self._update_buffer()
        if has_new_data:
            pass  # (re)calculate open/exit signals
        return has_new_data
