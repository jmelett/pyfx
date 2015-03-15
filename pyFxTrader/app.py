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
        '-c', '--cur',
        help='currency pairs, e.g. EUR_USD,USD_CHF',
        default='EUR_USD',
    )
    parser.add_argument(
        '-m', help='run mode', choices={'live', 'backtest'}, default='backtest'
    )

    args = parser.parse_args()
    controller = TradeController(
        mode=args.m,
        instruments=args.cur,
    )
    controller.start()
