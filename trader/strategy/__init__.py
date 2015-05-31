from collections import OrderedDict

import six
from logbook import Logger

from ..operations import Sell


log = Logger('pyFxTrader')


class StartegyBase(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self._is_open = False

    def open(self):
        self._is_open = True

    def start(self, broker, tick):
        self.broker = broker

    def tick(self, tick):
        return [
            Sell(self.instrument, 10),
        ]


class SMAStrategy(StartegyBase):
    timeframes = ['H1', 'H2']
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
                count=self.buffer_size,  # XXX: Or shall we limit by time?
            )

    def tick(self, tick):
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
            self.feeds[tf] = df

            # TODO:
            # self._convert_data(...)

        if has_changes:
            pass
