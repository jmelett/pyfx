# -*- coding: utf-8 -*-

from logbook import Logger

from lib.rfc3339 import datetimetostr, parse_datetime, parse_date

log = Logger('pyFxTrader')


class Broker(object):
    _initial_balance = 0.00
    _current_balance = 0.00

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
        start_date = parse_datetime('2015-02-01T00:00:00Z')
        end_date = parse_datetime('2015-02-10T00:00:00Z')
        # TODO Allow date to be passed as cli parameter

        tickdata_dict = {}

        for s in strategies:
            inst_dict = {}
            for tf in strategies[s].TIMEFRAMES:
                tf_dict = {}
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
                                continue
                        if tick_dt >= start_date:
                            candle_list.append(tick)
                        last_tick = tick_dt
                    if last_tick:
                        next_start = datetimetostr(last_tick)
                log.debug('Fetched %s candles for %s/%s' % (len(candle_list), s, tf))
                #print json.dumps(candle_list, indent=1)
                inst_dict[tf] = tf_dict
            tickdata_dict[strategies[s].instrument] = inst_dict
        self.backtest_data_ready = True
        return self.backtest_data_ready

    def get_history(self, **params):
        # TODO Implement backtest feed interface
        backtest = self.mode
        if self.mode == 'backtest':
            # Get data for defined timeframe (merge if neccessary)
            # On init provide 100, then 1 new candle
            raise NotImplementedError()
        elif self.mode == 'live':
            return self.api.get_history(**params)
        else:
            raise NotImplementedError()

    def get_account_balance(self):
        if not self.mode == 'backtest':
            raise NotImplementedError()
            self._current_balance = get_balance_from_api()
        return self._current_balance

    def get_open_trades(self):
        raise NotImplementedError()
