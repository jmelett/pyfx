from coolfig import Settings, Value, types, providers

from .strategy import SMAStrategy


class TraderSettings(Settings):
    ACCESS_TOKEN = Value(str)
    ACCOUNT_ID = Value(str)
    ENVIRONMENT = Value(str, default='practice')
    STRATEGY = Value(types.dottedpath, default=SMAStrategy)


settings = TraderSettings(providers.EnvConfig(prefix='TRADER_'))
