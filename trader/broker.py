from dateutil import parser as date_parse

import pandas as pd


class OandaBrokerBase(object):
    default_history_dataframe_columns = (
        'time',
        'volume',
        'complete',
        'openMid',
        'closeMid',
        'highMid',
        'lowMid',
    )

    def __init__(self, api):
        self._api = api

    def get_history(self, *args, **kwargs):
        columns = kwargs.pop('columns', self.default_history_dataframe_columns)
        if 'time' not in columns:
            columns = ('time',) + tuple(columns)
        response = self._api.get_history(*args, **kwargs)

        if response['candles']:
            df = pd.DataFrame(
                data=response['candles'],
                columns=columns,
            )
            df['time'] = df['time'].map(date_parse.parse)
            return df
        else:
            return pd.DataFrame()


class OandaBacktestBroker(OandaBrokerBase):
    def __init__(self, api, initial_balance):
        super(OandaBacktestBroker, self).__init__(api)
        self._current_balance = self._initial_balance = initial_balance

    def get_account_balance(self):
        return self._current_balance
