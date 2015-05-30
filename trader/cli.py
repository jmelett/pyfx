import decimal

import click

from .controller import Controller, IntervalClock
from .broker import OandaBacktestBroker
from .instruments import InstrumentParamType
from .strategy import TestStrategy


@click.command()
@click.option('--instrument', '-i', 'instruments', multiple=True,
              type=InstrumentParamType())
def main(instruments):
    """
    Algortihmic trading tool.
    """
    # XXX: Currently only backtesting is supported
    broker = OandaBacktestBroker(
        api=None, initial_balance=decimal.Decimal(1000))
    clock = IntervalClock(1)

    # XXX: We have to be able to instantiate strategies with custom args
    strategies = [TestStrategy(instrument) for instrument in set(instruments)]

    controller = Controller(clock, broker, strategies)
    controller.run_until_stopped()
