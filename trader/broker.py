from collections import OrderedDict
from decimal import Decimal, getcontext
from datetime import timedelta
from dateutil import parser as date_parse
from time import sleep
from math import log10
import logging

from OpenSSL.SSL import SysCallError
import pandas as pd
import pytz
from requests.packages.urllib3.exceptions import ProtocolError

from .lib.oandapy import OandaError
from .portfolio import Position


log = logging.getLogger('pyFx')


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
        print "Initialising backtest buffer.."
        for strategy in strategies:
            instrument = strategy.instrument
            timeframes = strategy.timeframes
            tf_dict = OrderedDict()

            for tf in timeframes:
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
                tf_dict[tf] = df
                print "Loaded {} candles for {}/{} ".format(
                    len(df), strategy.instrument, tf)
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
            if timeframe == 'H1' or timeframe == 'H2':
                current_df = self.feeds[instrument]['M5']
                current_df = current_df[(current_df.time > start) & (current_df.time < end)]
                current_row = current_df.tail(1)
                current_row.complete = False
                #current_row.loc[0, 'complete'] = False
                ret = pd.concat([ret, current_row])
        return ret


class OandaRealtimeBroker(OandaBrokerBase):
    def __init__(self, api, account_id):
        super(OandaRealtimeBroker, self).__init__(api)
        self._account_id = account_id
        self.last_transaction_id = None

    def get_account_balance(self):
        ret = self._api.get_account(self._account_id)
        if 'balance' in ret:
            return ret['balance']
        return False

    def get_price(self, instrument):
        params = {
            'instruments': str(instrument),
        }
        ret = self._api.get_prices(**params)
        if ret and 'prices' in ret and len(ret['prices']) > 0:
            return ret['prices'][0]
        return None

    def open_order(self, instrument, units, side, order_type,
                   price=None, expiry=None, stop_loss=None, take_profit=None):
        params = {
            'instrument': str(instrument),
            'units': units,
            'side': side,
            'type': order_type,
        }
        log.debug("[{}] Broker received open order.".format(instrument))
        # Available order_type's are:
        # 'limit', 'stop', 'marketIfTouched' or 'market'.

        if order_type in ['limit', 'stop', 'marketIfTouched']:
            if not price:
                raise ValueError(
                    "Price is required for OrderType {0:s}".format(order_type))
            if not expiry:
                expiry = (self._tick + timedelta(seconds=300)).isoformat()
                # raise ValueError("Expiration time is required for OrderType {0:s}".format(order_type))
            params['expiry'] = expiry

        if price:
            prec = abs(int(log10(float(instrument.pip))))
            new_price = round(price, prec)
            params['price'] = new_price

        #if stop_loss:
        #    params['stopLoss'] = stop_loss
        if take_profit:
            params['takeProfit'] = take_profit

        #else:
        #    if price:
        #        stop_loss_pips = (60 * float(instrument.pip))
        #        if side == 'buy':
        #            stop_loss_price = new_price - stop_loss_pips
        #        else:
        #            stop_loss_price = new_price + stop_loss_pips
        #        params['stopLoss'] = stop_loss_price

        #print params
        ret = None
        for _ in range(3):
            try:
                ret = self._api.create_order(self._account_id, **params)
                if ret:
                    break
            except OandaError as e:
                print "[!] Error while creating {} oder: {}. Retrying...".format(instrument, e)

        if not ret:
            return None
        ret_detail = ret.get('orderOpened', None)
        if not ret_detail:
            ret_detail = ret.get('tradeOpened', None)
        print ret, ret_detail
        if ret and 'price' in ret:
            if ret_detail and 'id' in ret_detail:
                pos = Position(
                    side=side,
                    instrument=instrument,
                    open_price=Decimal(ret['price']),
                    open_time=ret['time'],
                    order_id=ret_detail['id'],
                    order_type=order_type,
                )
                return pos
        return None

    def close_trade(self, position):
        # This method will block the rest, but it's important
        # that trades get closed immediately
        # while True:
        for _ in range(3):
            try:
                ret = self._api.close_trade(
                    self._account_id,
                    position.transaction_id
                )
                if all(k in ret for k in ('id', 'price', 'time', 'profit')):
                    position.close_price = ret['price']
                    position.profit_cash = ret['profit']
                    position.close_time = ret['time']
                    return position
                # TODO Check transactions
                else:
                    pass
            # TODO What if transaction was closed by broker?
            # TODO Handle Oanda exceptions properly
            except (ProtocolError, OandaError) as e:
                print "[!] Error during CLOSE action ({}). Trying again...".format(
                    e)
                sleep(3)
        return position
        return False

    def delete_pending_order(self, position):
        try:
            ret = self._api.close_order(
                account_id=self._account_id,
                order_id=position.order_id
            )
        except OandaError as e:
            print "[!] OandaError {}: {}".format(e.errno, e.strerror)
        return True

    def sync_transactions(self, position):
        # TODO Refactor this just to use api.get_transactions()
        # 1. Check if order is still PENDING

        # Since OANDA handles limit/market and stoploss/takeprofit orders
        # differently, we've to check both API endpoints.

        ret = None
        try:
            if position.order_type in ['limit', 'market', 'marketIfTouched']:
                ret = self._api.get_order(
                    account_id=self._account_id,
                    order_id=position.order_id)
            # TODO Handle 'takeprofit' properly in Portfolio Class
            if position.order_type in ['stop', 'takeprofit']:
                ret = self._api.get_trade(
                    account_id=self._account_id,
                    trade_id=position.order_id)
        except OandaError as e:
            print e
            pass

        if ret and 'id' in ret:
            return "PENDING"

        # 2. Since no order/trade was found, check if it was executed
        ret = self._api.get_transaction_history(
            account_id=self._account_id)
        if ret and "transactions" in ret:
            for trans in ret['transactions']:
                transaction_id = trans.get('id', None)
                transaction_type = trans.get('type', None)
                transaction_price = trans.get('price', None)
                transaction_stoploss = trans.get('stopLossPrice', None)
                order_id = trans.get('orderId', None)

                if position.order_type == 'market':
                    if transaction_id == position.order_id:
                        if transaction_type in ['MARKET_ORDER_CREATE',]:
                            position.open_price = transaction_price
                            position.transaction_id = transaction_id
                            position.stop_loss = transaction_stoploss
                            return "CONFIRMED"
                else:
                    if order_id and order_id == position.order_id:
                        if transaction_type in ['ORDER_FILLED',
                                                'STOP_LOSS_FILLED',
                                                'TAKE_PROFIT_FILLED',
                                                'TRAILING_STOP_FILLED']:
                            if transaction_id:
                                position.open_price = transaction_price
                                position.transaction_id = transaction_id
                                position.stop_loss = transaction_stoploss
                                return "CONFIRMED"
        # 3. Lastly, if ID isn't showing up anymore, return the info
        return "NOTFOUND"
