import os

from coolfig import Settings, Value, types, providers

from .strategy.sma_example import SmaStrategy


class TraderSettings(Settings):
    ACCESS_TOKEN = Value(str)
    ACCOUNT_ID = Value(str)
    ENVIRONMENT = Value(str, default='practice')
    STRATEGY = Value(types.dottedpath, default=SmaStrategy)


settings = TraderSettings(
       providers.DictConfig(os.environ, prefix='TRADER_'))
