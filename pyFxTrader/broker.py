class Broker:
    _initial_balance = 0.00
    _current_balance = 0.00

    mode = None

    def __init__(self, mode):
        self.mode = mode
        if not self.mode == 'backtesting':
            self._initial_balance = self._get_account_balance()
        else:
            self._initial_balance = 10000
            self._current_balance = self._initial_balance

    def get_account_balance(self):
        if not self.mode == 'backtesting':
            raise NotImplementedError()
            self._current_balance = get_balance_from_api()
        return self._current_balance
