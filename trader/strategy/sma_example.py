import time

from logbook import Logger
import numpy as np
import pandas as pd
import talib
import matplotlib.pyplot as plt

from . import Strategy


log = Logger('pyFxTrader')

SMA_FAST = 10
SMA_SLOW = 50


class SmaStrategy(Strategy):
    STRATEGY_NAME = 'SmaCrossingStrategy'
    TIMEFRAMES = ['H1', 'H2']

    def __init__(self, *args, **kwargs):
        super(SmaStrategy, self).__init__(*args, **kwargs)

    def _convert_data(self, feed, timeframe):
        if not feed:
            return None

        close_array = []
        open_array = []
        volume_array = []
        time_array = []
        time_formatted_array = []
        for item in feed:
            close_array.append(item['closeMid'])
            open_array.append(item['openMid'])
            volume_array.append(float(item['volume']))
            time_array.append(item['time'])
            time_formatted_array.append(item['time'][11:16])

        close_array = np.asarray(close_array)
        volume_array = np.asarray(volume_array)

        sma_fast_array = talib.SMA(np.array(close_array), 4)
        sma_slow_array = talib.SMA(np.array(close_array), 9)
        _, _, macd_array = talib.MACD(close_array,  # macd, signal, hist
                                      fastperiod=12,
                                      slowperiod=26,
                                      signalperiod=9)
        rsi_array = talib.RSI(np.array(close_array))

        ret_df = pd.DataFrame(data={
            'time': time_formatted_array,
            'time_full': time_array,
            'close': close_array,
            'open': open_array,
            'volume': volume_array,
            'sma_fast': sma_fast_array,
            'sma_slow': sma_slow_array,
            'macd': macd_array,
            'rsi': rsi_array,
        })
        self.pretty_plot(ret_df, timeframe, self.STRATEGY_NAME)
        return ret_df

    def pretty_plot(self, df, timeframe, title):
        df.tail(30).plot(x='time',
                         y=['close', 'sma_fast', 'sma_slow', ])
        plt.suptitle('%s/%s (%s), %s' % (
            self.instrument, timeframe, title, time.strftime("%c")))
        plt.savefig(u'plots/{0:s}_{1:s}'.format(self.instrument, timeframe))

    def start(self):
        pass

    def recalc(self, backtest=False):
        has_new_data = self._update_buffer()
        if has_new_data:
            pass  # (re)calculate open/exit signals
        return has_new_data
