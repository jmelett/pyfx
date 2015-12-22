from dateutil import parser as date_parse
from time import sleep

from OpenSSL.SSL import SysCallError
import pandas as pd
from requests.packages.urllib3.exceptions import ProtocolError

from ..lib.oandapy import OandaError


class OandaBrokerBase(object):
    default_history_dataframe_columns = (
        'time',
        'volume',
        'complete',
        'closeBid',
        'closeAsk',
        'openBid',
        'openAsk',
        'highBid',
        'highAsk',
        'lowBid',
        'lowAsk',
    )

    def __init__(self, api):
        self._api = api
        self._tick = None

    def get_instrument_detail(self, instrument):
        params = {'instruments': instrument}
        ret = self._api.get_instruments(self._account_id, **params)
        return ret

    def set_current_tick(self, tick):
        self._tick = tick

    def get_history(self, *args, **kwargs):
        columns = kwargs.pop('columns', self.default_history_dataframe_columns)
        include_current = kwargs.pop('include_current', False)
        if 'time' not in columns:
            columns = ('time',) + tuple(columns)
        while True:
            try:
                response = None
                response = self._api.get_history(*args, **kwargs)
                if response and response.get('candles'):
                    df = pd.DataFrame(
                        data=response['candles'],
                        columns=columns,
                    )
                    df['time'] = df['time'].map(date_parse.parse)
                    df['closeMid'] = df[['closeBid','closeAsk']].mean(axis=1)
                    if not include_current:
                        df = df[df.complete == True]
                    return df
                else:
                    return pd.DataFrame()
            except (ValueError) as e:
                print "[!] Error when loading candles for {}: {}".format(kwargs['instrument'], e)
                return pd.DataFrame()
            except (ProtocolError, OandaError, SysCallError) as e:
                print "[!] Connection error ({0:s}). Reconnecting...".format(e)
            sleep(3)

    def get_price(self, instrument):
        raise NotImplementedError()

    def open_order(self, instrument, units, side, order_type,
                   price=None, expiry=None, stop_loss=None, take_profit=None):
        raise NotImplementedError()

    def sync_transactions(self, position):
        raise NotImplementedError()

    def delete_pending_order(self, position):
        raise NotImplementedError()

    def close_trade(self, position):
        raise NotImplementedError()
