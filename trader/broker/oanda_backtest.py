import logging
import os
from collections import OrderedDict
from decimal import Decimal, getcontext
from datetime import timedelta
from dateutil import parser as date_parse

import pandas as pd
import pytz
import warnings

from .base import OandaBrokerBase
from ..app_conf import settings
from ..portfolio import Position

log = logging.getLogger('pyFx')


class OandaBacktestBroker(OandaBrokerBase):
    pip_to_cash = 1000.00 * 50 ## conversion from pip to cash(?)
    time_delta = timedelta(seconds=1)
    timeframe_delta = {
        'H2': timedelta(minutes=120),
        'H1': timedelta(minutes=60),
        'M15': timedelta(minutes=15),
        'M5': timedelta(minutes=5),
    }

    def __init__(self, api, account_id, initial_balance):
        super(OandaBacktestBroker, self).__init__(api)
        self._current_balance = self._initial_balance = initial_balance
        self._transaction_id = 0
        self._account_id = account_id

    def _get_id(self):
        self._transaction_id += 1
        return self._transaction_id

    def get_price(self, instrument):
        # TODO Return via tick
        return None

    def get_account_balance(self):
        return self._current_balance

    def open_order(self, instrument, units, side, order_type,
                   price=None, expiry=None, stop_loss=None, take_profit=None):

        pos = Position(
            side=side,
            instrument=instrument,
            open_price=Decimal(price),
            open_time=self._tick,
            order_id=self._get_id(),
            order_type=order_type,
        )
        pos.transaction_id = pos.order_id
        return pos

    def close_trade(self, position):
        '''Close a position'''
        price = position.close_price
        if position.side == 'buy':
            profit = price - position.open_price
        else: ## if position.side == 'sell':
            profit = position.open_price - price
        position.profit_pips = profit / Decimal(str(position.instrument.pip))
        position.close_time = self._tick

        # 0.0001/1.137*1014*50
        position.profit_cash = round(float(position.profit_pips) *\
            float(position.instrument.pip)/float(price) * self.pip_to_cash, 2)

        return position

    def sync_transactions(self, position):
        '''Interface'''
        return 'CONFIRMED'

    def delete_pending_order(self, position):
        '''Interface'''
        return True

    def M5_injection(self, df, tf, tf_dict):
        '''Inject M5 candles within the H1 and H2 dataframes.'''
        df.loc[:,'tf'] = tf
        M5_candles = tf_dict['M5']
        M5_candles.loc[:,'tf'] = 'M5'
        M5_candles.complete = False

        df = pd.concat([df, M5_candles])
        df = df.sort_index(kind='mergesort')

        return df

    def init_backtest(self, start, end, strategies):
        '''
        First method to be ran which loads all the strategies and timeframes
        into memory. It either loads the info from HDF stores in disk or queries
        the API.
        '''
        # Silence pandas errors
        pd.options.mode.chained_assignment = None
        warnings.filterwarnings('ignore', \
            category=pd.io.pytables.PerformanceWarning)

        self.feeds = OrderedDict()
        log.info('Initialising backtest buffer...')
        stores_dir = settings.BACKTEST_STORES_DIR
        if not os.path.exists(stores_dir):
            os.makedirs(stores_dir)
        for strategy in strategies:
            instrument = strategy.instrument

            store_fname = (
                '{}/history-{}-{}-{}-{}.h5'
                .format(
                    stores_dir,
                    strategy.__class__.__name__,
                    instrument,
                    start.strftime('%s'),
                    end.strftime('%s'),
                )
            )
            store = pd.HDFStore(store_fname, mode='a')
            timeframes = strategy.timeframes
            tf_dict = OrderedDict()

            ## ensure M5 candles are processed first
            tf_order = ['M5', 'M15', 'H1', 'H2']
            timeframes = [tf for tf in tf_order if tf in timeframes]

            ## fetch the timeframe from disk if it was already
            ## downloaded otherwise download it through the API
            for tf in timeframes:
                if tf in store:
                    source = 'HDFStore'
                    df = store[tf]
                    log.debug('loading data from HDFstore {}/{}'.format(
                              store.filename, tf))
                else:
                    source = 'API'
                    df = pd.DataFrame(
                         columns=self.default_history_dataframe_columns)

                    # TODO Make sure first candle gets loaded without hack

                    ## load earlier data so initial backtesting buffer
                    ## is not completely empty
                    next_start = (start - timedelta(days=2)).isoformat()

                    while next_start != None:

                        data_buffer = super(OandaBacktestBroker, self).get_history(
                            instrument=instrument,
                            granularity=tf,
                            candleFormat='bidask',
                            start=next_start,
                            includeFirst='false',
                            count=2000,
                        )
                        if data_buffer.empty:
                            break
                        last_tick = data_buffer.tail(1).time.values[0].replace(
                            tzinfo=pytz.utc)
                        if last_tick > end:
                            ## achieve same result as (df.time <= end)
                            data_buffer = data_buffer[:end]
                            next_start = None
                        else:
                            next_start = last_tick.isoformat()

                        df = pd.concat([df, data_buffer])

                    ## inject current_candles
                    if tf in {'H1', 'H2'}:
                        df = self.M5_injection(df, tf, tf_dict)

                    log.debug('saving data to HDFstore {}/{}'.format(
                        store.filename, tf))
                    ## save df to disk
                    df.to_hdf(store, tf)

                ## store df in memory
                tf_dict[tf] = df

                log.info("loaded {} candles for {}/{} (from {})".format(
                    df.shape[0], strategy.instrument, tf, source))

            store.close()
            self.feeds[instrument] = tf_dict

        return True

    def get_history(self, *args, **kwargs):

        instrument = kwargs.get('instrument')
        timeframe = kwargs.get('granularity')
        start = kwargs.get('start')
        end = kwargs.get('end')
        include_current = kwargs.get('include_current', False)

        df = self.feeds[instrument][timeframe]
        start = date_parse.parse(start)
        end = date_parse.parse(end)

        start_main = start + self.time_delta
        end_main = end - self.timeframe_delta.get(timeframe)

        if timeframe in {'H1', 'H2'} and include_current:
            ## achieve same result as (df.time > start) & (df.time < end)
            M5_start = end - self.timeframe_delta.get('M5') * 2
            M5_end = end - self.timeframe_delta.get('M5')

            df = df[start_main:M5_end]
            df = df.loc[(df.index <= end_main) & (df.tf == timeframe) | \
                (df.index > M5_start) & (df.tf == 'M5')]
        else:
            ## achieve same result as (df.time > start) & (df.time <= end_main)
            df = df[start_main:end_main]
            if timeframe in {'H1', 'H2'}:
                df = df.loc[(df.tf == timeframe)]

        return df
