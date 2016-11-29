from coolfig import Settings, Value, types, providers


class TraderSettings(Settings):
    # Account
    ACCESS_TOKEN = Value(str)
    ACCOUNT_ID = Value(str)
    ENVIRONMENT = Value(str, default='practice')

    STRATEGY = Value(types.dottedpath)
    CLOCK_INTERVAL = Value(int, default=30)
    BACKTEST_START = Value(str, default='2015.07.15')
    BACKTEST_END = Value(str, default='2015.07.16')
    BACKTEST_STORES_DIR = Value(str, default='tmp/stores')
    GET_INCOMPLETE_CANDLES = True

    DEFAULT_INSTRUMENTS = Value(types.list(str), default=[
        'AUD_USD',
        'AUD_JPY',
        'EUR_USD',
        'EUR_GBP',
        'GBP_USD',
        'NZD_JPY',
        'USD_JPY',
        'GBP_CHF',
        'USD_CHF',
        'USD_CAD',
        'EUR_CHF',
        'DE30_EUR',
        'JP225_USD',
        'UK100_GBP',
        'HK33_HKD',
        'BCO_USD',
        'XAG_USD',
        'XAU_USD',
    ])

    # Portfolio
    DEFAULT_POSITION_MARGIN = Value(float, 1000.00)
    PF_USE_STOPLOSS_CALC = Value(types.boolean, True)
    PF_USE_TAKE_PROFIT_DOUBLE = Value(types.boolean, False)

    # Communication
    TELEGRAM_TOKEN = Value(str)
    TELEGRAM_CHAT_ID = Value(str)

    # Strategy specific
    MYSTRATEGY_SMA_FAST = Value(int, default=10)
    MYSTRATEGY_SMA_SLOW = Value(int, default=20)
    MYSTRATEGY_RSI5_BARS = Value(int, default=65)
    MYSTRATEGY_RSI15_BARS = Value(int, default=24)
    MYSTRATEGY_USE_RSI15 = Value(types.boolean, default=True)

    # Em Strategy
    EM_USE_M5 = Value(types.boolean, default=False)
    EM_EXIT_CURRENT = Value(types.boolean, default=False)
    EM_USE_LIMIT_ORDER = Value(types.boolean, default=True)
    EM_MAX_TIMEDELTA = Value(int, default=3600)
    EM_USE_DOUBLE_CONFIRM = Value(types.boolean, default=True)


settings = TraderSettings(providers.EnvConfig(prefix='TRADER_'))
