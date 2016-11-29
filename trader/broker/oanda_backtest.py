import logging
import os
from collections import OrderedDict
from decimal import Decimal, getcontext
from datetime import timedelta
from dateutil import parser as date_parse

import pandas as pd
import pytz

from .base import OandaBrokerBase
from ..app_conf import settings
from ..portfolio import Position


log = logging.getLogger('pyFx')


class OandaBacktestBroker(OandaBrokerBase):
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
        price = position.close_price
        if position.side == 'buy':
            profit = price - position.open_price
        else:
            profit = position.open_price - price
        position.profit_pips = profit / Decimal(str(position.instrument.pip))
        position.close_time = self._tick

        #0.0001/1.137*1014*50
        position.profit_cash = round(float(position.profit_pips) * float(position.instrument.pip)/float(price) * 1000.00 * 50, 2)

        return position

    def sync_transactions(self, position):
        return 'CONFIRMED'

    def delete_pending_order(self, position):
        return True

    def init_backtest(self, start, end, strategies):
        self.feeds = OrderedDict()
        log.info('Initialising backtest buffer..')
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

            for tf in timeframes:
                if tf in store:
                    source = 'HDFStore'
                    df = store[tf]
                    log.debug('loading data from HDFstore {}/{}'.format(store.filename, tf))
                else:
                    source = 'API'
                    next_start = None
                    df = pd.DataFrame(
                        columns=self.default_history_dataframe_columns)

                    while True:
                        if not next_start:
                            # TODO Make sure first candle get loaded without hack
                            next_start = (start - timedelta(seconds=1)).isoformat()
                        data = super(OandaBacktestBroker, self).get_history(
                            instrument=instrument,
                            granularity=tf,
                            candleFormat='bidask',
                            start=next_start,
                            includeFirst='false',
                            count=2000,
                        )
                        if data.empty:
                            break
                        last_tick = data.tail(1).time.values[0].replace(
                            tzinfo=pytz.utc)
                        df = df.append(data, ignore_index=True)
                        if last_tick >= end and len(df) > 0:
                            df = df[df.time <= end]
                            break
                        next_start = last_tick.isoformat()

                    log.debug('saving data to HDFstore {}/{}'.format(store.filename, tf))
                    df.to_hdf(store, tf)

                tf_dict[tf] = df
                log.info("loaded {} candles for {}/{} (from {})".format(
                    len(df), strategy.instrument, tf, source))

            store.close()
            self.feeds[instrument] = tf_dict

        return True

    def get_history(self, *args, **kwargs):
        timeframe_delta = {
            'H2': timedelta(minutes=120),
            'H1': timedelta(minutes=60),
            'M15': timedelta(minutes=15),
            'M5': timedelta(minutes=5),
        }
        instrument = kwargs.get('instrument')
        timeframe = kwargs.get('granularity')
        start = kwargs.get('start')
        end = kwargs.get('end')
        include_current = kwargs.get('include_current', False)

        if end and not start:
            return super(OandaBacktestBroker, self).get_history(
                *args, **kwargs)

        df = self.feeds[instrument][timeframe]
        start = date_parse.parse(start)
        end = date_parse.parse(end)

        end_main = end - timeframe_delta.get(timeframe)
        ret = df[(df.time > start) & (df.time <= end_main)]

        # Silence pandas errors
        pd.options.mode.chained_assignment = None

        # Adding current candle via M5 df
        if include_current and timeframe:
            if timeframe in {'H1', 'H2'}:
                current_df = self.feeds[instrument]['M5']
                current_df = current_df[(current_df.time > start) & (current_df.time < end)]
                current_row = current_df.tail(1)
                current_row.complete = False
                #current_row.loc[0, 'complete'] = False
                ret = pd.concat([ret, current_row])
        return ret

