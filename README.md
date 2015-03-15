pyFxTrader
=========


# Scope

- The goal is to write a backtesting AND live trading tool, which can execute
  multiple strategies on up to 10 currency pairs.
- Strategies can monitor up to three timeframes (e.g. H1, H2 and D1) and 
  calculate buy/sell actions based on them.


# Strategy

## Indicators

Currently implemented are

- MACD
- SMA
- RSI

Many others can also be used from `TA-Lib` or `numpy`.


## Timeframes

* OANDA supports a wide range of timeframes. You can find all supported values [here](http://developer.oanda.com/rest-live/rates/#retrieveInstrumentHistory).


# TODO

- Add Matplot/Plot.ly support. See also following [tutorial](http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/).
- Implement proxy class for backtesting, which will first check if data is 
  available locally and only then fetch/save via API.
- Implement usage of ETags to reduce traffic/latency
- Prepare Makefile


# Installation

    git clone git@github.com:jmelett/pyFxTrader.git
    cd pyFxTrader
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    python pyFxTrader/app.py -h
