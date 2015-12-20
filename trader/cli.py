# -*- coding: utf-8 -*-

import decimal
from time import strftime
from dateutil import parser
import sys
import logging

import click
import pytz
from rainbow_logging_handler import RainbowLoggingHandler

from .app_conf import settings
from .broker import OandaBacktestBroker, OandaRealtimeBroker
from .controller import Controller, SimulatedClock, IntervalClock
from .instruments import InstrumentParamType
from .lib import oandapy
from .portfolio import Portfolio


DEFAULT_INSTRUMENTS = [
    'AUD_USD',
    'AUD_JPY',
    'EUR_USD',
    'EUR_GBP',
    'GBP_USD',
    'NZD_JPY',
    'USD_JPY',
    'GBP_CHF',
    'USD_CHF',
    'USD_CAD',
    'EUR_CHF',
    # 'DE30_EUR',
    # 'JP225_USD',
    # 'UK100_GBP',
    # 'HK33_HKD',
    'BCO_USD',
    'XAG_USD',
    'XAU_USD',
]


@click.command()
@click.option('--instrument', '-i', 'instruments',
              default=DEFAULT_INSTRUMENTS,
              multiple=True,
              type=InstrumentParamType())
@click.option('--mode', '-m', 'mode', default='backtest',
              type=click.Choice(['backtest', 'live']))
@click.option('--start', '-s', 'start_date',)
@click.option('--end', '-e', 'end_date',)
@click.option('--log', '-l', 'log_level',
              default='info',
              type=click.Choice(['info', 'debug', 'warning',]))

def main(instruments, mode, log_level, start_date=None, end_date=None):
    """
    Algorithmic trading tool.
    """

    # Make urllib3 logger more calm
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.CRITICAL)

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)
    log_filename = "logs/pyfx_debug_{}-{}.log".format(strftime("%Y_%m_%d-%H_%M"), settings.ENVIRONMENT)
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)
    logger = logging.getLogger('pyFx')

    formatter = logging.Formatter("[%(asctime)s/%(levelname)s] %(funcName)s():%(lineno)d\t%(message)s")
    handler = RainbowLoggingHandler(sys.stdout, color_funcName=('black', 'yellow', True))
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)
    logger.addHandler(handler)

    start_date_ = start_date if start_date else settings.BACKTEST_START
    end_date_ = end_date if end_date else settings.BACKTEST_END
    BACKTEST_START = parser.parse(start_date_).replace(tzinfo=pytz.utc)
    BACKTEST_END = parser.parse(end_date_).replace(tzinfo=pytz.utc)

    if mode == 'backtest':
        api = oandapy.API(
            environment=settings.ENVIRONMENT,
            access_token=settings.ACCESS_TOKEN,
        )
        broker = OandaBacktestBroker(
            api=api,
            account_id=settings.ACCOUNT_ID,
            initial_balance=decimal.Decimal(5000))

        # Oanda 20:00, Local: 22:00, DailyFx: 16:00
        clock = SimulatedClock(
            start=BACKTEST_START,
            stop=BACKTEST_END,
            interval=settings.CLOCK_INTERVAL,
        )

    elif mode == 'live':
        api = oandapy.API(
            environment=settings.ENVIRONMENT,
            access_token=settings.ACCESS_TOKEN,
        )
        clock = IntervalClock(interval=settings.CLOCK_INTERVAL)
        broker = OandaRealtimeBroker(api=api, account_id=settings.ACCOUNT_ID)
    else:
        raise NotImplementedError()

    # TODO Optimize load of instrument info
    instrument_list = set(instruments)
    for inst in instrument_list:
        inst.load(broker)
    # TODO We have to be able to instantiate strategies with custom args
    strategies = [settings.STRATEGY(instrument)
                  for instrument in instrument_list]
    if mode == 'backtest':
        broker.init_backtest(BACKTEST_START, BACKTEST_END, strategies)
        pf = Portfolio(broker, mode='backtest')
    else:
        pf = Portfolio(broker, mode='live')
    controller = Controller(clock, broker, pf, strategies)
    controller.run_until_stopped()
