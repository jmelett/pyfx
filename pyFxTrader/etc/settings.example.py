""" Example settings file for pyFxTrader """

from strategy.sma_example import SmaStrategy


# OANDA API Access Key
ACCESS_TOKEN = ''

# OANDA Account ID
ACCOUNT_ID = ''

# Default environment: live, practice or sandbox
DEFAULT_ENVIRONMENT = 'practice'

# Default Strategy
DEFAULT_STRATEGY = SmaStrategy