from decimal import Decimal
from datetime import timedelta
from time import sleep
from math import log10
import logging

from requests.packages.urllib3.exceptions import ProtocolError

from .base import OandaBrokerBase
from ..lib.oandapy import OandaError
from ..portfolio import Position


log = logging.getLogger('pyFx')


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
