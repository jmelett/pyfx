# -*- coding: utf-8 -*-

import csv
import os
from collections import OrderedDict
from decimal import Decimal
import itertools
import time
import logging

from .app_conf import settings
from .utils import assert_decimal

log = logging.getLogger('pyFx')


class Open(object):
    def __init__(self, strategy, price, side, order_type='limit'):
        self.strategy = strategy
        self.price = assert_decimal(price)
        self.side = side
        self.order_type = order_type

    def __call__(self, portfolio):
        portfolio.open_order(
            strategy=self.strategy,
            side=self.side,
            order_type=self.order_type,
            price=self.price,
        )


class Close(object):
    def __init__(self, strategy, price):
        self.strategy = strategy
        self.price = assert_decimal(price)

    def __call__(self, portfolio):
        portfolio.close_trade(self.strategy, price=self.price)


class Portfolio(object):
    def __init__(self, broker, mode='live'):

        self.broker = broker
        self.mode = mode

        self.pending_order_list = []  # Pending orders
        self.position_list = []  # Confirmed transactions
        self.csv_out_file = 'logs/backtest_log-{}.csv'.format(
            time.strftime("%Y%m%d-%H%M%S"))

        if mode == 'live':
            import telegram
            self.telegram = telegram.Bot(token=settings.TELEGRAM_TOKEN)

    def send_bot(self, message):
        if self.mode == 'live' and self.telegram:
            try:
                self.telegram.sendMessage(
                    chat_id=settings.TELEGRAM_CHAT_ID,
                    text=message)
                return True
            except Exception, e:
                log.warn("TELEGRAM ERROR: {}".format(e))
        return False

    def open_order(self, strategy, side, order_type,
                   price=None, expiry=None, stop_loss=None):

        units = self.calculate_position_size(strategy.instrument)

        if (not stop_loss and settings.PF_USE_STOPLOSS_CALC):
            stoploss_price = self.calculate_stop_loss(strategy.instrument, side)
        else:
            stoploss_price = stop_loss

        # stoploss_price = stop_loss
        takeprofit_price = self.calculate_take_profit(strategy.instrument,
                                                          side)
        if settings.PF_USE_TAKE_PROFIT_DOUBLE:
            units = int(units / 2)

            position_1 = self.broker.open_order(
                instrument=strategy.instrument,
                units=units,
                side=side,
                order_type=order_type,
                price=price,
                expiry=expiry,
                stop_loss=stoploss_price,
                take_profit=takeprofit_price,
            )
            position_2 = self.broker.open_order(
                instrument=strategy.instrument,
                units=units,
                side=side,
                order_type=order_type,
                price=price,
                expiry=expiry,
                stop_loss=stoploss_price,
            )
            if position_1:
                strategy.open_position(position_1)
                self.pending_order_list.append(position_1)
                open_msg = "Open 1/2 {} ORDER #{} for {}/{} at {}".format(
                    position_1.side,
                    position_1.order_id, position_1.instrument,
                    position_1.open_price,
                    position_1.open_time)
                log.info(open_msg)
                self.send_bot(open_msg)
            if position_2:
                strategy.open_position(position_2)
                self.pending_order_list.append(position_2)
                open_msg = "Open 2/2 {} ORDER #{} for {}/{} at {}".format(
                    position_2.side,
                    position_2.order_id, position_2.instrument,
                    position_2.open_price,
                    position_2.open_time)
                log.info(open_msg)
                self.send_bot(open_msg)
            if position_1 and position_2:
                return True
        else:
            position = self.broker.open_order(
                instrument=strategy.instrument,
                units=units,
                side=side,
                order_type=order_type,
                price=price,
                expiry=expiry,
                stop_loss=stoploss_price,
                take_profit=takeprofit_price,
            )
            if position:
                strategy.open_position(position)
                self.pending_order_list.append(position)
                open_msg = "Open {} ORDER #{} for {}/{} at {}".format(
                    position.side,
                    position.order_id, position.instrument,
                    position.open_price,
                    position.open_time)
                log.info(open_msg)
                self.send_bot(open_msg)
                return True
        return False

    def close_trade(self, strategy, price=None):
        pos_to_remove = []
        for pos in strategy.positions:
            # Pending orders
            if pos in self.pending_order_list:
                if self.broker.delete_pending_order(pos):
                    self.pending_order_list.remove(pos)
            # Active transaction
            elif pos in self.position_list:
                # Hack to make backtests work, will get overwritten by real broker
                if price:
                    pos.close_price = assert_decimal(price)
                ret = self.broker.close_trade(pos)
                if ret:
                    pos.close()
                    close_msg = "Close TRADE #{} for {}/{} at {} [PROFIT: {}/Total: {}]".format(
                        pos.transaction_id, pos.instrument,
                        pos.close_price, pos.close_time,
                        pos.profit_cash, self.get_overall_profit())
                    log.info(close_msg)
                    self.send_bot(close_msg)
                    self.write_to_csv(pos)
                    pos_to_remove.append(pos)
            else:
                pos_to_remove.append(pos)
                # raise ValueError("Critical error: Position was not "
                #                 "registered with application.")
        for pos in  pos_to_remove:
            strategy.close_position(pos)
        return True

    def run_operations(self, operations, strategies):
        # TODO: Add risk management/operations consolidation here
        # Limit by % of the whole portfolio when buying/selling
        # Per instrument only one open position
        # handling exit signals

        # TODO: Check if there is a buy/sell, then ignore
        # TODO: Run open()'s first, then update_transactions(), then close()'s
        for ops in itertools.chain(*operations):
            ops(self)
        self.update_transactions(strategies)

    def update_transactions(self, strategies):
        # TODO Here we should check all orders and transactions
        for pos in self.pending_order_list:
            ret = self.broker.sync_transactions(pos)
            if ret == 'PENDING':
                continue
            elif ret == 'CONFIRMED':
                self.pending_order_list.remove(pos)
                self.position_list.append(pos)
            elif ret == 'NOTFOUND':
                # TODO This can be done in a more elegant way
                self.pending_order_list.remove(pos)
                for s in strategies:
                    for p in s.positions:
                        if pos == p:
                            s.close_position(pos)
                            break
        return True

    def write_to_csv(self, position):
        add_headings = not os.path.isfile(self.csv_out_file)
        with open(self.csv_out_file, 'at') as fh:
            items = OrderedDict(
                open_time=position.open_time,
                close_time=position.close_time,
                instrument=position.instrument,
                side=position.side,
                open_price=position.open_price,
                close_price=position.close_price,
                profit_cash=position.profit_cash,
                profit_pips=position.profit_pips,
                max_profit_pips=position.max_profit_pips,
                max_loss_pips=position.max_loss_pips,
            )

            writer = csv.writer(fh)
            if add_headings:
                writer.writerow(items.keys())
            writer.writerow(items.values())

    def get_overall_profit(self):
        total_profit = 0
        for pos in self.position_list:
            profit = getattr(pos, 'profit_cash')
            if profit:
                total_profit += profit
        return total_profit

    def calculate_position_size(self, instrument):
        # Based on http://fxtrade.oanda.com/analysis/margin-calculator
        margin = settings.DEFAULT_POSITION_MARGIN
        margin_ratio = 50
        home_currency = 'CHF'
        base_currency = instrument.from_curr

        currency_switch_dict = {
            'JP225_CHF': 12500,
            'DE30_CHF': 10000,
            'AUD_CHF': 0.68,
            'BCO_CHF': 38.46,
            'NZD_CHF': 0.61101,
            'XAU_CHF': 1063.82,
            'CHF_CHF': 1,  # Meh
            'GBP_CHF': 1.4749,
            'USD_CHF': 0.93586,
            'EUR_CHF': 1.08053,
            'XAG_CHF': 13.736,
            'HK33_CHF': 2631.57,
            'UK100_CHF': 8333,
        }
        # (margin * leverage) / base = units
        currency_pair = "{}_{}".format(base_currency, home_currency)
        base_home_price = currency_switch_dict.get(currency_pair, None)

        position_size = 10
        if base_home_price:
            position_size = int((margin * margin_ratio / (base_home_price)))

        multiplier_dict = {
            'EUR_USD' : 2,
            'EUR_GBP' : 2,
            'GBP_USD' : 2,
            'NZD_JPY' : 2,
            'USD_JPY' : 2,
            'GBP_CHF' : 2,
            'USD_CHF' : 2,
            'USD_CAD' : 2,
            'EUR_CHF' : 2,
        }

        position_size = position_size * multiplier_dict.get(currency_pair, 1)
        return position_size

    def calculate_stop_loss(self, instrument, side):
        stop_loss_dict = {
            'XAG_USD': 350,
            'EUR_USD': 20,
            'UK100_GBP': 9,
            'NZD_JPY': 15,
            'BCO_USD': 40,
            'AUD_USD': 9,
            'DE30_EUR': 40,
            'HK33_USD': 70,
            'USD_JPY': 20,
            'XAU_USD': 300,
        }
        stop_loss_pips = float(stop_loss_dict.get(str(instrument), 20))
        price = self.broker.get_price(instrument)
        if price:
            if side == 'buy':
                return Decimal(price['bid']) - Decimal(
                    (stop_loss_pips * float(str(instrument.pip))))
            return Decimal(price['ask']) + Decimal(
                (stop_loss_pips * float(str(instrument.pip))))
        return None

    def calculate_take_profit(self, instrument, side):
        take_profit_dict = {
            'AUD_USD': 27,
            'AUD_JPY': 8,
            'EUR_CHF': 10,
            'EUR_USD': 12,
            'EUR_GBP': 12,
            'GBP_CHF': 12,
            'GBP_USD': 15,
            'NZD_JPY': 8,
            'USD_CAD': 12,
            'USD_CHF': 15,
            'USD_JPY': 8,
            'BCO_USD': 25,
            'DE30_EUR': 20,
            'HK33_HKD': 9,
            'JP225_USD': 25,
            'UK100_GBP': 20,
            'XAG_USD': 340,
            'XAU_USD': 400,
        }
        take_profit_pips = float(take_profit_dict.get(str(instrument), 20))
        price = self.broker.get_price(instrument)
        if price:
            if side == 'buy':
                return Decimal(price['ask']) + Decimal(
                    (take_profit_pips * float(str(instrument.pip))))
            return Decimal(price['bid']) - Decimal(
                (take_profit_pips * float(str(instrument.pip))))
        return None


class Position(object):
    def __init__(self, side, instrument, open_price, open_time,
                 order_id, order_type, stop_loss=None, home_currency='CHF'):
        self.side = side
        self.instrument = instrument
        self.open_price = assert_decimal(open_price)
        self.open_time = open_time
        self.order_id = order_id
        self.order_type = order_type
        if stop_loss:
            self.stop_loss = assert_decimal(stop_loss)
        self.home_currency = home_currency

        self.is_open = True
        self.profit_pips = None
        self.profit_cash = None
        self.transaction_id = None
        self.close_price = None
        self.close_time = None

        self.max_profit = open_price
        self.max_loss = open_price

        # TODO If required, add order_type, stop_loss, expiry_date

    def close(self):
        self.is_open = False

    def set_profit_loss(self, price):
        # Min = Max Drawdown for StopLoss
        # Max = Max Profit
        # Both are initialised with the opening price
        if self.side == 'buy':
            if self.max_profit < Decimal(str(price.highBid)):
                self.max_profit = Decimal(str(price.highBid))
            if self.max_loss > Decimal(str(price.lowAsk)):
                self.max_loss = Decimal(str(price.lowAsk))
        else:
            if self.max_profit > Decimal(str(price.lowBid)):
                self.max_profit = Decimal(str(price.lowBid))
            if self.max_loss < Decimal(str(price.highAsk)):
                self.max_loss = Decimal(str(price.highAsk))
        self.max_profit_pips = round(abs(
            float(float(self.max_profit) - float(self.open_price)) / float(
                str((self.instrument.pip)))), 1)
        self.max_loss_pips = round(abs(
            float(float(self.open_price) - float(self.max_loss)) / float(
                str((self.instrument.pip)))), 1)

    def __str__(self):
        return "{} at {} [{}]".format(self.instrument, self.open_price,
                                      self.open_time)
