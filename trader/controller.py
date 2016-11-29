import multiprocessing

import os
import threading
import signal
import logging
from datetime import datetime, timedelta
from time import sleep

import click


log = logging.getLogger('pyFx')


class IntervalClock(object):
    def __init__(self, interval):
        self.interval = interval

    def __iter__(self):
        while True:
            yield datetime.utcnow()
            sleep(self.interval)


class SimulatedClock(object):
    def __init__(self, start, stop, interval):
        self.start = start
        self.stop = stop
        self.interval = timedelta(seconds=interval)

    def __iter__(self):
        current = self.start
        while current < self.stop:
            yield current
            current += self.interval


class ControllerBase(object):
    """
    A controller class takes care to run the actions returned by the strategies
    for each clock tick. How exactly this is implemented is deferred to the
    concrete subclass.
    """

    def __init__(self, clock, broker, portfolio, strategies):
        self._clock = clock
        self._broker = broker
        self._strategies = strategies
        self._portfolio = portfolio

    def initialize(self, tick):
        for strategy in self._strategies:
            strategy.start(self._broker, tick)

    def run(self):
        raise NotImplementedError()

    def run_until_stopped(self):
        raise NotImplementedError()

    def is_running(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def execute_tick(self, tick):
        raise NotImplementedError()


class SingleThreadedControllerMixin(object):
    def __init__(self, *args, **kwargs):
        super(SingleThreadedControllerMixin, self).__init__(*args, **kwargs)
        self._stop_requested = False
        self._is_running = False

    def run(self):
        raise NotImplementedError()

    def run_until_stopped(self):
        def stop(signal, frame):
            self.stop()

        signal.signal(signal.SIGINT, lambda signal, frame: self.stop())
        self._is_running = True
        try:
            clock = iter(self._clock)
            self.initialize(next(clock))
            for tick in clock:
                if self._stop_requested:
                    break
                self.execute_tick(tick)
                if self._stop_requested:
                    break
            else:
                log.info('The clock stopped ticking')
        finally:
            self._is_running = False

    def is_running(self):
        return self._is_running

    def stop(self):
        log.warning('\nSIGINT received, shutting down cleanly...')
        self._stop_requested = True


class Controller(SingleThreadedControllerMixin, ControllerBase):
    def execute_tick(self, tick):
        # Broker needs to know the current tick for backtesting & logging
        # TODO Solve in a more elegant way
        self._broker.set_current_tick(tick)

        operations = [strategy.tick(tick) for strategy in self._strategies]
        operations = [op for op in operations if op]

        # This will execute the new operations (and further required tasks)
        self._portfolio.run_operations(operations, self._strategies)

