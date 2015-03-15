#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import signal
import sys

from controller import TradeController


def signal_handler(signal, frame):
    print '\n[-] Disconnecting, good bye.'
    controller.disconnect()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        __file__,
        description='Algorithmic trading tool'
    )
    parser.add_argument(
        '-c',
        dest='currencies',
        default='EUR_USD,USD_CHF',
        help='currency pairs, e.g. EUR_USD,USD_CHF',
    )
    parser.add_argument(
        '-m',
        dest='mode',
        choices={'live', 'backtest'},
        default='backtest',
        help='run mode',
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbosity',
        default=0,
        action='count',
        help='increase verbosity')

    args = parser.parse_args()

    controller = TradeController(
        mode=args.mode,
        instruments=args.currencies,
    )
    controller.start()
