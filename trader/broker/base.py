import logging
from dateutil import parser as date_parse
from time import sleep

from OpenSSL.SSL import SysCallError
import pandas as pd
from requests.packages.urllib3.exceptions import ProtocolError

from ..lib.oandapy import OandaError

log = logging.getLogger('pyFx')


class OandaBrokerBase(object):
    '''
    Base class for broker objects. Not to be instantiated by itself, always as
    part of a child class.
    '''
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
        '''
        Query the API for a given instrument and timeframe and return its df.
        '''
        columns = kwargs.pop('columns', self.default_history_dataframe_columns)
        include_current = kwargs.pop('include_current', False)
        if 'time' not in columns:
            columns = ('time',) + tuple(columns)
        while True:
            try:
                response = self._api.get_history(*args, **kwargs)
                if response and response.get('candles'):
                    df = pd.DataFrame(
                        data=response['candles'],
                        columns=columns,
                    )
                    df['time'] = df['time'].map(date_parse.parse)
                    df['closeMid'] = df.loc[:,('closeBid','closeAsk')].mean(axis=1)
                    df.index = df['time']
                    if not include_current:
                        df = df[df.complete == True]
                    return df
                else:
                    log.info("no history for {} and timeframe {}".format(
                             kwargs['instrument']), kwargs['granularity'])
                    return pd.DataFrame()
            except ValueError as e:
                log.warning("[!] Error when loading candles for {}: {}".format(
                            kwargs['instrument'], e))
                return pd.DataFrame()
            except (ProtocolError, OandaError, SysCallError) as e:
                log.warning("[!] Connection error ({0:s}). Reconnecting...".format(e))
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
