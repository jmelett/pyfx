# -*- coding: utf-8 -*-

from collections import deque

from logbook import Logger

log = Logger('pyFxTrader')


class Strategy(object):
    TIMEFRAMES = []  # e.g. ['M30', 'H2']
    BUFFER_SIZE = 500
    INIT_BAR_COUNT = 100
    NEXT_BAR_COUNT = 10

    def __init__(self, instrument, broker):
        self.instrument = instrument
        self.broker = broker

        if not self.TIMEFRAMES:
            raise ValueError('Please define TIMEFRAMES variable.')
        self.feeds = {}
        for tf in self.TIMEFRAMES:
            self.feeds[tf] = deque(maxlen=self.BUFFER_SIZE)
            log.info('Initialized %s feed for %s' % (tf, self.instrument))

    def _convert_data(self, feed):
        raise NotImplementedError()

    def start(self):
        """ Called on strategy start. """
        raise NotImplementedError()

    def new_bar(self, instrument, cur_index):
        """ Called on every bar of every instrument that client is subscribed on. """
        raise NotImplementedError()

    def execute(self, engine, instruments, cur_index):
        """ Called on after all indicators have been updated for this bar's index """
        raise NotImplementedError()

    def end(self, engine):
        """ Called on strategy stop. """
        raise NotImplementedError()

    def update_buffer(self):
        """ Update update buffer with latest feed data """

        for timeframe in self.feeds:
            last_timestamp = None
            if len(self.feeds[timeframe]) > 0:
                response = self.broker.get_history(
                    instrument=self.instrument,
                    granularity=timeframe,
                    count=self.NEXT_BAR_COUNT, )
                last_timestamp = self.feeds[timeframe][-1]['time']
            else:
                response = self.broker.get_history(
                    instrument=self.instrument,
                    granularity=timeframe,
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
                log.debug('{0:d} new candle(s) for {1:s}/{2:s}'.format(
                    len(new_candles), timeframe, self.instrument))
                new_candles = sorted(new_candles, key=lambda k: k['time'])
                # print json.dumps(new_candles, indent=1)
                for candle in new_candles:
                    self.feeds[timeframe].append(candle)

                self.data_buffer[timeframe] = self._convert_data(
                    self.feeds[timeframe])

        if new_candles:
            return True
        else:
            return False
