import click


class Instrument(object):
    def __init__(self, from_curr, to_curr):
        self.from_curr = from_curr
        self.to_curr = to_curr

    def __str__(self):
        return '{}_{}'.format(self.from_curr, self.to_curr)


class InstrumentParamType(click.ParamType):
    name = 'instrument'

    def convert(self, value, param, ctx):
        try:
            currencies = value.split('_')
            assert len(currencies) == 2
            return Instrument(currencies[0], currencies[1])
        except (AssertionError, ValueError):
            self.fail('{} is not a valid instrument'.format(value), param, ctx)
