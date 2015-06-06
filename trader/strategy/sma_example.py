from collections import OrderedDict

import six
import talib

from ..operations import Close, OpenBuy
from . import StrategyBase


class SMAStrategy(StrategyBase):
    timeframes = ['M5', 'M15']
    sma_intervals = {
        'sma_fast': 10,
        'sma_slow': 50,
    }
    buffer_size = 300

    def start(self, broker, tick):
        super(SMAStrategy, self).start(broker, tick)

        self.feeds = OrderedDict()
        for tf in self.timeframes:
            self.feeds[tf] = broker.get_history(
                instrument=self.instrument,
                granularity=tf,
                end=tick.isoformat(),
                candleFormat='midpoint',
                count=self.buffer_size,
            )

    def tick(self, tick):
        has_changes = False
        new_candles = OrderedDict()
        for tf, df in six.iteritems(self.feeds):
            response = self.broker.get_history(
                instrument=self.instrument,
                granularity=tf,
                candleFormat='midpoint',
                includeFirst='false',
                end=tick.isoformat(),
                start=df.iloc[-1].name.isoformat(),
            )
            if response.empty:
                continue

            has_changes = True
            new_candles[tf] = response
            df = df.append(response)[-self.buffer_size:]
            self.feeds[tf] = self.annotate_data(df, tf)

        if has_changes:
            if self.is_open:
                # Searching for CloseSignal
                return self.find_close_signal()
            else:
                # Searching for OpenSignal
                return self.find_open_signal(new_candles)

    def annotate_data(self, feed, timeframe):
        # Get SMAs
        for k, v in six.iteritems(self.sma_intervals):
            feed[k] = talib.SMA(feed['closeMid'].values, v)

        # Get MACD
        # NOTE: talib.MACD() returns (macd, signal, hist)
        _, _, feed['macd_hist'] = talib.MACD(feed['closeMid'].values,
                                             fastperiod=12,
                                             slowperiod=26,
                                             signalperiod=9)

        # Get RSI
        feed['rsi'] = talib.RSI(feed['closeMid'].values)
        return feed

    def find_open_signal(self, new_candles):
        return [
            OpenBuy(self, self.instrument, 10),
        ]

    def find_close_signal(self):
        return [
            Close(self, self.instrument, 10),
        ]
