==========
pyFxTrader
==========

.. image:: https://travis-ci.org/jmelett/pyFxTrader.svg
    :target: https://travis-ci.org/jmelett/pyFxTrader

.. image:: https://img.shields.io/github/license/mashape/apistatus.svg
    :target: https://github.com/jmelett/pyFxTrader/blob/master/LICENSE


Scope
=====

* The goal is to provide a backtesting and live trading tool, which can run
  multiple strategies on up to 10 currency pairs.
* Strategies can monitor up to three timeframes (e.g. H1, H2 and D1) and 
  calculate buy/sell actions based on them.


Strategy
========

Indicators
----------

Besides building your own, you can also use a wide range of indicators via `TA-Lib` or `numpy`.


Timeframes
----------

* OANDA supports most commonly used timeframes. You can find all supported values here_.
.. _here: http://developer.oanda.com/rest-live/rates/#retrieveInstrumentHistory.


TODO
====

* Add Matplot/Plot.ly support. See also following tutorial_.
.. _tutorial: http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/.
* Implement proxy class for backtesting, which will first check if data is 
  available locally and only then fetch/save via API.
* Implement usage of ETags to reduce traffic/latency.
* Prepare Makefile.

Requirements
============

    sudo apt-get install virtualenv python-setuptools libssl-dev::
    
    sudo apt-get build-dep python-matplotlib

Additionally get TA-Lib from http://www.ta-lib.org/hdr_dw.html

Installation
============

::

    git clone git@github.com:jmelett/pyfx.git
    cd pyfx
    virtualenv env
    source env/bin/activate
    pip install -e .
    envdir .my_envs python ./_cmd.py -h

Troubleshooting
===============

In case you encounter the error ```ImportError: libta_lib.so.0: cannot open shared object file: No such file or directory```

Following command\* will do the trick: ```export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH```

\* See also http://stackoverflow.com/questions/11813279/python-wrapper-for-ta-lib-import-failure
