# -*- coding: utf-8 -*-

import decimal
import errno
import logging
import os
import sys
from time import strftime, time
from dateutil import parser

import click
import pytz
from rainbow_logging_handler import RainbowLoggingHandler

try:
    import ipdb as pdb
except ImportError:
    import pdb

from .app_conf import settings
from .broker.oanda_backtest import OandaBacktestBroker
from .broker.oanda_live import OandaRealtimeBroker
from .controller import Controller, SimulatedClock, IntervalClock
from .instruments import InstrumentParamType
from .lib import oandapy
from .portfolio import Portfolio

log = logging.getLogger('pyFx')


def hr(char='-', width=None, **kwargs):
    if width is None:
        width = click.get_terminal_size()[0]
    click.secho(char * width, **kwargs)


@click.command()
@click.option('--instrument', '-i', 'instruments',
              default=settings.DEFAULT_INSTRUMENTS,
              multiple=True,
              type=InstrumentParamType())
@click.option('--mode', '-m', 'mode', default='backtest',
              type=click.Choice(['backtest', 'live']))
@click.option('--start', '-s', 'start_date', )
@click.option('--end', '-e', 'end_date', )
@click.option('--log', '-l', 'log_level',
              default='info',
              type=click.Choice(['info', 'debug', 'warning', ]))
@click.option('-d', '--debug', default=False, is_flag=True,
              help=('Drop into the debugger if the command execution raises '
                    'an exception.'))
@click.option('--step', default=False, is_flag=True,
              help='Step into debugger at the start of the program')
def main(instruments, mode, log_level, debug, step, start_date=None,
         end_date=None):
    """
    Algorithmic trading tool.
    """

    _start_time = time()
    if debug:
        def exception_handler(type, value, traceback):
            click.secho(
                '\nAn exception occurred while executing the requested '
                'command:', fg='red'
            )
            hr(fg='red')
            sys.__excepthook__(type, value, traceback)
            click.secho('\nStarting interactive debugging session:', fg='red')
            hr(fg='red')
            pdb.post_mortem(traceback)

        sys.excepthook = exception_handler

    if step:
        pdb.set_trace()

    # Make urllib3 logger more calm
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.CRITICAL)

    try:
        os.makedirs('logs')
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)
    log_filename = "logs/pyfx_debug_{}-{}.log".format(
        strftime("%Y_%m_%d-%H_%M"), settings.ENVIRONMENT)
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s/%(levelname)s] %(funcName)s():%(lineno)d\t%(message)s")
    handler = RainbowLoggingHandler(
        sys.stdout, color_funcName=('black', 'yellow', True))
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)
    log.addHandler(handler)

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
        clock_interval = settings.CLOCK_INTERVAL
        log.info('Starting simulated clock with interval {} seconds'.format(clock_interval))
        clock = SimulatedClock(
            start=BACKTEST_START,
            stop=BACKTEST_END,
            interval=clock_interval,
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

    log.info('script duration: {:.2f}s'.format(time() - _start_time))
