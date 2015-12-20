# -*- coding: utf-8 -*-

from collections import OrderedDict
from decimal import Decimal

import six
import talib

from . import StrategyBase
from ..portfolio import Close, Open


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
                count=self.buffer_size,
            )

    def tick(self, tick):
        has_changes = False
        new_candles = OrderedDict()
        current_candle = OrderedDict()
        for tf, df in six.iteritems(self.feeds):
            response = self.broker.get_history(
                instrument=self.instrument,
                granularity=tf,
                includeFirst='false',
                start=df.iloc[-1].time.isoformat(),
                end=tick.isoformat(),
            )
            if not response.empty:
                new_candles[tf] = response
                df = df.append(response, ignore_index=True)[-self.buffer_size:]
                self.feeds[tf] = self.annotate_data(df, tf)

                if current_candle:
                     current_candle[tf] = current_candle

                has_changes = True
        if has_changes:
            if self.is_open:
                # Searching for CloseSignal
                close_ops = self.find_close_signal(new_candles, current_candle=None, tick=tick)
                if close_ops and hasattr(close_ops, "__iter__"):
                    open_ops = self.find_open_signal(new_candles, current_candle=None, tick=tick)
                    if open_ops and hasattr(open_ops, "__iter__"):
                        close_ops.extend(open_ops)
                return close_ops
            else:
                # Searching for OpenSignal
                return self.find_open_signal(new_candles, current_candle=None, tick=tick)

    def annotate_data(self, feed, timeframe):
        # Get SMAs
        for k, v in six.iteritems(self.sma_intervals):
            feed[k] = talib.SMA(feed['closeMid'].values, v)

        # Get MACD
        # NOTE: talib.MACD() returns (macd, signal, hist)
        feed['macd'], _, feed['macd_hist'] = talib.MACD(
            feed['closeMid'].values,
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )

        # Get RSI
        feed['rsi'] = talib.RSI(feed['closeMid'].values)
        return feed

    def find_open_signal(self, new_candles):
        return [Open(self, side='buy', price=Decimal(1.0)), ]

    def find_close_signal(self, new_candles):
        return [Close(self, price=Decimal(1.2)), ]
