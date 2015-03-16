# -*- coding: utf-8 -*-

from logbook import Logger

log = Logger('pyFxTrader')


class Broker(object):
    _initial_balance = 0.00
    _current_balance = 0.00

    mode = None
    api = None

    def __init__(self, mode, api, initial_balance=10000.00):
        self.mode = mode
        self.api = api

        log.debug(u'Broker mode: {0:s}'.format(self.mode))
        if self.mode == 'backtest':
            self._initial_balance = initial_balance
            self._current_balance = self._initial_balance
        else:
            self._initial_balance = self.get_account_balance()
        log.debug('Balance: %f/%f' % (self._initial_balance, self._current_balance))

    def get_history(self, **params):
        # TODO Implement backtest feed interface
        backtest = False
        if backtest:
            raise NotImplementedError()
        else:
            return self.api.get_history(**params)

    def get_account_balance(self):
        if not self.mode == 'backtest':
            raise NotImplementedError()
            self._current_balance = get_balance_from_api()
        return self._current_balance

    def get_open_trades(self):
        raise NotImplementedError()
