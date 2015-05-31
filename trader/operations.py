import click


class Sell(object):
    def __init__(self, strategy, instrument, amount):
        self.strategy = strategy
        self.instrument = instrument
        self.amount = amount

    def __call__(self, broker):
        click.echo('Selling {} {}'.format(self.amount, self.instrument))
        self.strategy.open()
