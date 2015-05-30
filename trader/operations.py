import click


class Sell(object):
    def __init__(self, instrument, amount):
        self.instrument = instrument
        self.amount = amount

    def __call__(self, broker):
        click.echo('Selling {} {}'.format(self.amount, self.instrument))
