import click

from .utils import assert_decimal


class OpenBase(object):
    def __init__(self, strategy, instrument, amount):
        self.strategy = strategy
        self.instrument = instrument
        self.amount = assert_decimal(amount)

    def __call__(self, broker):
        raise NotImplementedError()


class OpenBuy(OpenBase):
    def __call__(self, broker):
        click.echo('Buying {} {}'.format(self.amount, self.instrument))
        self.strategy.open('a transaction id')


class OpenSell(OpenBase):
    def __call__(self, broker):
        click.echo('Selling {} {}'.format(self.amount, self.instrument))
        self.strategy.open('a transaction id')


class Close(object):
    def __init__(self, strategy, instrument, amount):
        self.strategy = strategy
        self.instrument = instrument
        self.amount = assert_decimal(amount)

    def __call__(self, broker):
        click.echo('Closing {} {}'.format(self.amount, self.instrument))
        self.strategy.close()
