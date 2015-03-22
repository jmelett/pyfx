# -*- coding: utf-8 -*-

from collections import deque

from logbook import Logger

log = Logger('pyFxTrader')


class Strategy(object):
    TIMEFRAMES = []  # e.g. ['M30', 'H2']
    BUFFER_SIZE = 300
    INIT_BAR_COUNT = 100
    NEXT_BAR_COUNT = 10

    def __init__(self, instrument, broker):
        self.instrument = instrument
        self.broker = broker

        self.feeds = {}
        self.data_frame = {}

        if not self.TIMEFRAMES:
            raise ValueError('Please define TIMEFRAMES variable.')
        for tf in self.TIMEFRAMES:
            self.feeds[tf] = deque(maxlen=self.BUFFER_SIZE)
            log.info('Initialized %s feed for %s' % (tf, self.instrument))

    def _convert_data(self, feed, timeframe):
        """
        Converts feed input to a dataframe, which can be used
        for further data analysis
        """

        raise NotImplementedError()

    def _update_buffer(self):
        """
        Update update buffer with latest feed data
        the get_history() method is called here since this can be very
        strategy specific.
        """
        # TODO Needs refactoring for better integration in Broker class.

        has_changes = False
        new_candles_dict = {}

        for timeframe in self.feeds:
            last_timestamp = None
            if len(self.feeds[timeframe]) > 0:
                response = self.broker.get_history(
                    instrument=self.instrument,
                    granularity=timeframe,
                    candleFormat='midpoint',
                    count=self.NEXT_BAR_COUNT, )
                last_timestamp = self.feeds[timeframe][-1]['time']
            else:
                response = self.broker.get_history(
                    instrument=self.instrument,
                    granularity=timeframe,
                    candleFormat='midpoint',
                    count=self.INIT_BAR_COUNT, )

            new_candles = []
            for candle in response['candles']:
                candle_timestamp = candle['time']
                if last_timestamp:
                    if candle_timestamp > last_timestamp:
                        new_candles.append(candle)
                else:
                    new_candles.append(candle)

            if new_candles:
                has_changes = True
                log.debug('{0:d} new candle(s) for {1:s}/{2:s}'.format(
                    len(new_candles), timeframe, self.instrument))
                new_candles = sorted(new_candles, key=lambda k: k['time'])
                # print json.dumps(new_candles, indent=1)
                for candle in new_candles:
                    self.feeds[timeframe].append(candle)

                self.data_frame[timeframe] = self._convert_data(
                    self.feeds[timeframe], timeframe)
            new_candles_dict[timeframe] = len(new_candles)
        return has_changes, new_candles_dict

    def start(self):
        """ Called on strategy start. """
        raise NotImplementedError()

    def end(self):
        """ Called on strategy stop. """
        raise NotImplementedError()

    def recalc(self):
        """ Update buffer and recalculate signals. """
        raise NotImplementedError()

