from collections import OrderedDict

import six
from logbook import Logger
import talib

from ..operations import Close, OpenBuy, OpenSell
from . import StrategyBase

log = Logger('pyFxTrader')

SMA_FAST = 10
SMA_SLOW = 50


class SMAStrategy(StrategyBase):
    timeframes = ['M5', 'M15']
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
        print tick
        has_changes = False
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
            df = df.append(response)[-self.buffer_size:]
            self.feeds[tf] = self._convert_data(df, tf)

        if has_changes:
            if self._is_open:
                # Searching for ExitSignal
                return [Close(self, self.instrument, 10), ]
            else:
                # Searching for OpenSignal
                return [OpenBuy(self, self.instrument, 10), ]

    def _convert_data(self, feed, timeframe):
        # Get SMAs
        feed['sma_fast'] = talib.SMA(feed['closeMid'].values, SMA_FAST)
        feed['sma_slow'] = talib.SMA(feed['closeMid'].values, SMA_SLOW)

        # Get MACD
        # Note: talib.MACD() returns (macd, signal, hist)
        _, _, macd_array = talib.MACD(feed['closeMid'].values,
                                      fastperiod=12,
                                      slowperiod=26,
                                      signalperiod=9)

        # Get RSI
        feed['rsi'] = talib.RSI(feed['closeMid'].values)
        return feed
