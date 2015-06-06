from decimal import Decimal


def assert_decimal(val):
    if isinstance(val, Decimal):
        return val

    if isinstance(val, (int, str)):
        return Decimal(val)

    raise ValueError("value is required to be of type 'decimal', "
                     "but it is of type {!r}".format(type(val).__name__))
