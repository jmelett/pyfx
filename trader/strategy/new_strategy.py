# -*- coding: utf-8 -*-

from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from datetime import timedelta
import logging

import six
import talib
import pytz

from . import StrategyBase

from ..app_conf import settings
from ..portfolio import Close, Open


class NewStrategy(StrategyBase):
    """A strategy for demonstrating how a strategy should be built.

    This strategy simply closes a postion, if there is an open position, and
    opens a position at 5 minutes intervals if new candles exist.
    """
    time_delta = timedelta(seconds=1)
    timeframe_delta = {
        'H2': timedelta(minutes=120),
        'H1': timedelta(minutes=60),
        'M15': timedelta(minutes=15),
        'M5': timedelta(minutes=5),
    }
    mode = 'backtest'  # or set to 'live'
    tick_tf = 'M5'  # keep it at 'M5' until later versions
    timeframes = ['M5', 'M15', 'H1', 'H2']
    buffer_size = 300
    sma_intervals = {
        'sma_fast': 10,
        'sma_slow': 50,
    }

    def start(self, broker, tick):
        self.check_timeframes()
        super(NewStrategy, self).start(broker, tick)
        self.feeds = OrderedDict()
        self.last_tick = tick
        self.last_ticks = {tf: self.last_tick for tf in self.timeframes}
        self.last_candles = {tf: self.last_tick - self.time_delta for tf in
                             self.timeframes}

    def check_timeframes(self):
        """ Ensure timeframes are in ascending order """
        tf_order = ['M5', 'M15', 'H1', 'H2']
        timeframes = [tf for tf in tf_order if tf in self.timeframes]

        if self.timeframes != timeframes:
            raise Exception("Timeframes list in strategy must be in ascending "
                            "order in length.")

    def _tick_tf_time_check(self, tick):
        """Check if enough ticks have passed for new tick_tf candle or new
        current candle to appear.
        """
        if self.mode == 'backtest':
            if (tick - self.last_tick) >= self.timeframe_delta[self.tick_tf]:
                self.last_tick = tick
                return True
            else:
                return False
        elif self.mode == 'live':
            return True
        else:
            raise ValueError("Strategy mode must be set to 'backtest' or "
                             "'live'")

    def _tf_time_check(self, tick, tf):
        """Check if enough ticks have passed for new tf candle or new current
        candle to appear.
        """
        if self.mode == 'backtest':
            if settings.GET_INCOMPLETE_CANDLES or (
                        tick - self.last_ticks[tf]) >= \
                    self.timeframe_delta[tf]:
                self.last_ticks[tf] = tick
                return True
        else:
            self._tick_tf_time_check(tick)

    def _compare_dates(self, df, tf):
        """Check if new candles came in, otherwise there is a lapse in
        trading data and no new annotations should be done.
        """
        has_changes = False
        if df.empty:
            return has_changes
        else:
            newest_time = df.tail(1).time.values[0]
            if newest_time > self.last_candles[tf]:
                has_changes = True
                self.last_candles[tf] = newest_time

        return has_changes

    def _has_changes(self, df, tf,
                     include_current=settings.GET_INCOMPLETE_CANDLES):
        """Check if new candles came in, otherwise there is a lapse in
        trading data and no new annotations should be done.

        In backtesting, changes for H1 and H2 timeframes are based on changes
        on M5. This function helps gain minor time benefits from this fact.
        """
        if include_current and self.mode == 'backtest':
            if tf == self.tick_tf:
                self.tick_tf_changes = self._compare_dates(df, tf)
                has_changes = self.tick_tf_changes
            elif tf in {'H1', 'H2'}:
                has_changes = self.tick_tf_changes
            else:  # When tf is 'M15' for example
                has_changes = self._compare_dates(df, tf)
        else:
            has_changes = self._compare_dates(df, tf)

        return has_changes

    def tick(self, tick):
        """Process strategy at each tick"""
        position_ops = None

        if self._tick_tf_time_check(tick):
            has_changes = False

            for tf in self.timeframes:
                if self._tf_time_check(tick, tf):
                    # Query buffer_size of candles
                    start = tick - (
                        (self.buffer_size + 1) * self.timeframe_delta[tf]
                    ) + self.time_delta
                    df = self.broker.get_history(
                        instrument=self.instrument,
                        granularity=tf,
                        includeFirst='false',
                        start=start.isoformat(),
                        end=tick.isoformat(),
                        include_current=settings.GET_INCOMPLETE_CANDLES,
                    )

                    # Check if there is a lapse in trading data
                    if self._has_changes(df, tf):
                        has_changes = True
                        self.feeds[tf] = self.annotate_data(df, tf)

            if has_changes:
                if self.is_open:
                    # Searching for CloseSignal
                    close_ops = self.find_close_signal(self.feeds, tick=tick)
                    if close_ops and hasattr(close_ops, "__iter__"):
                        open_ops = self.find_open_signal(self.feeds, tick=tick)
                        if open_ops and hasattr(open_ops, "__iter__"):
                            close_ops.extend(open_ops)
                    position_ops = close_ops
                else:
                    # Searching for OpenSignal
                    position_ops = self.find_open_signal(self.feeds, tick=tick)

        return position_ops

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

    def find_open_signal(self, feeds, tick):
        """Open a position at time tick."""
        if not tick:
            raise ValueError('Tick value is required for this strategy.')

        for key in feeds:
            price = feeds[key].tail(1).closeAsk
            price = Decimal(str(price.values[0]))
            return [Open(self, side='buy', price=price)]

    def find_close_signal(self, feeds, tick):
        """Close a position at time tick, if a positon exists."""
        for key in feeds:
            price = feeds[key].tail(1)

            for p in self.positions:
                p.set_profit_loss(price)
            price = feeds[key].tail(1).closeBid
            price = Decimal(str(price.values[0]))
            return [Close(self, price=price)]
