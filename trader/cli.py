import decimal
from datetime import datetime

import click

from .controller import Controller, SimulatedClock
from .broker import OandaBacktestBroker
from .instruments import InstrumentParamType
from .lib import oandapy
from .conf import settings


@click.command()
@click.option('--instrument', '-i', 'instruments', multiple=True,
              type=InstrumentParamType())
def main(instruments):
    """
    Algortihmic trading tool.
    """
    # XXX: Currently only backtesting is supported
    api = oandapy.API(
        environment='sandbox',
        access_token=settings.ACCESS_TOKEN,
    )
    broker = OandaBacktestBroker(
        api=api, initial_balance=decimal.Decimal(1000))

    clock = SimulatedClock(
        start=datetime(2015, 01, 01, 12, 00),
        stop=datetime(2015, 01, 01, 13, 00),
        interval=300,
    )

    # XXX: We have to be able to instantiate strategies with custom args
    strategies = [settings.STRATEGY(instrument)
                  for instrument in set(instruments)]

    controller = Controller(clock, broker, strategies)
    controller.run_until_stopped()
