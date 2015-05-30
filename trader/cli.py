import click

from .controller import ThreadedController, IntervalClock
from .broker import BacktestBroker
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
    broker = BacktestBroker()
    clock = IntervalClock(1)

    # XXX: We have to be able to instantiate strategies with custom args
    strategies = [TestStrategy(instrument) for instrument in set(instruments)]

    controller = ThreadedController(clock, broker, strategies)
    controller.run_until_stopped()
