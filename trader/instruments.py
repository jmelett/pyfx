import click


class Instrument(object):
    def __init__(self, from_curr, to_curr, pip=None, max_trade_units=None):
        self.from_curr = from_curr
        self.to_curr = to_curr
        self.pip = pip
        self.max_trade_units = max_trade_units

    def __str__(self):
        return '{}_{}'.format(self.from_curr, self.to_curr)

    def __repr__(self):
        return self.__str__()

    def load(self, broker):
        print "[+] Loading details for {}".format(self.__str__())
        ret = broker.get_instrument_detail(self.__str__())
        if ret and 'instruments' in ret:
            for meh in ret['instruments']:
                self.pip = meh['pip']
                self.max_trade_units = meh['maxTradeUnits']
                return True
        return False


class InstrumentParamType(click.ParamType):
    name = 'instrument'

    def convert(self, value, param, ctx):
        try:
            currencies = value.split('_')
            assert len(currencies) == 2
            return Instrument(currencies[0], currencies[1])
        except (AssertionError, ValueError):
            self.fail('{} is not a valid instrument'.format(value), param, ctx)
