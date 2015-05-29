# -*- coding: utf-8 -*-

from datetime import timedelta

from logbook import Logger

from .lib.rfc3339 import datetimetostr, parse_datetime

log = Logger('pyFxTrader')


class Broker(object):
    _initial_balance = 0.00
    _current_balance = 0.00

    # backtesting vars
    _backtest_start_datetime = None
    _backtest_tick_buffer = None

    mode = None
    api = None
    backtest_data_ready = False

    def __init__(self, mode, api, initial_balance=10000.00):
        self.mode = mode
        self.api = api
        self.backtest_data_ready = False

        log.debug(u'Broker mode: {0:s}'.format(self.mode))
        if self.mode == 'backtest':
            self._initial_balance = initial_balance
            self._current_balance = self._initial_balance
        else:
            self._initial_balance = self.get_account_balance()
        log.debug(
            'Balance: %f/%f' % (self._initial_balance, self._current_balance))

    def init_backtest_data(self, strategies):
        """
        Prepare the backtest data for each strategy and timeframe and save
        it in a dictionary, which is afterwards accessed by the get_history()
        method.
        """

        start_date = parse_datetime('2015-03-20T00:00:00Z')
        end_date = parse_datetime('2015-03-24T00:00:00Z')
        # TODO Allow datetime to be passed as cli parameter
        self._backtest_start_datetime = start_date
        self._backtest_tick_buffer = tickdata_dict = {}

        for s in strategies:
            instrument_dict = {}
            for tf in strategies[s].TIMEFRAMES:
                is_data_downloaded = False

                candle_list = []
                last_tick = None
                next_start = None
                while not is_data_downloaded:
                    if not next_start:
                        next_start = datetimetostr(start_date)
                    data = self.api.get_history(
                        instrument=s,
                        granularity=tf,
                        candleFormat='midpoint',
                        start=next_start,
                        includeFirst='true',
                        count=5000)
                    if len(data['candles']) <= 1:
                        break
                    for tick in data['candles']:
                        tick_dt = parse_datetime(tick['time'])
                        if tick_dt > end_date:
                            is_data_downloaded = True
                            break
                        if last_tick:
                            if tick_dt <= last_tick:
                                # Ignore if new tick value is older than the
                                # last_tick
                                raise ValueError(
                                    "Received tick in non-sequential order")
                                # continue
                        if tick_dt >= start_date:
                            candle_list.append(tick)
                        last_tick = tick_dt
                    if last_tick:
                        next_start = datetimetostr(last_tick)
                log.debug(
                    'Fetched %s candles for %s/%s' % (len(candle_list), s, tf))
                # print json.dumps(candle_list, indent=1)
                instrument_dict[tf] = candle_list
            tickdata_dict[strategies[s].instrument] = instrument_dict
        self.backtest_data_ready = True
        return self.backtest_data_ready

    def get_history(self, **params):
        if self.mode == 'backtest':
            # Get data for defined timeframes:
            # On init provide 100, then "simulate" the current time and provide
            # relative candles
            if 'is_init' in params:
                # TODO Fixme: Provide 100 candles BEFORE 'start' date
                data = self.api.get_history(
                    instrument=params['instrument'],
                    granularity=params['granularity'],
                    candleFormat=params['candleFormat'],
                    start=datetimetostr(self._backtest_start_datetime),
                    includeFirst='true',
                    count=100)
                return data

            self._backtest_start_datetime = (self._backtest_start_datetime +
                                             timedelta(seconds=30))
            tick_data = self._backtest_tick_buffer[params['instrument']][
                params['granularity']]

            ret_list = []
            for item in tick_data:
                tick_time = parse_datetime(item['time'])
                if tick_time <= self._backtest_start_datetime:
                    ret_list.append(item)
            tick_data = [x for x in tick_data if x not in ret_list]

            if len(tick_data) <= 0:
                exit()  # TODO Move this to controller (or strategy)

            self._backtest_tick_buffer[params['instrument']][
                params['granularity']] = tick_data
            return {'candles': ret_list}

        elif self.mode == 'live':
            return self.api.get_history(**params)
        else:
            raise NotImplementedError()

    def get_account_balance(self):
        if not self.mode == 'backtest':
            raise NotImplementedError()
            # self._current_balance = get_balance_from_api()
        return self._current_balance

    def get_open_trades(self):
        raise NotImplementedError()
