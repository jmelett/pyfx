import threading
import itertools
from time import sleep

import click


class IntervalClock(object):
    def __init__(self, interval):
        self.interval = interval

    def __iter__(self):
        while True:
            # XXX: We probably want to return a datetime here
            yield
            sleep(self.interval)


class DummyClock(object):
    def __iter__(self):
        while True:
            yield


class ThreadedController(object):
    def __init__(self, clock, broker, strategies):
        self._stop_requested = False
        self._main_loop = None
        self.clock = clock
        self.broker = broker
        self.strategies = strategies

    def run(self):
        assert self._main_loop is None
        self._main_loop = threading.Thread(target=self._run)
        self._main_loop.start()

    def run_until_stopped(self):
        self.run()
        while True:
            try:
                sleep(999)
            except KeyboardInterrupt:
                self.stop()
                break

    def _run(self):
        for tick in self.clock:
            if self._stop_requested:
                return
            self.execute_tick(tick)
            if self._stop_requested:
                return

    def execute_tick(self, tick):
        operations = [strategy.tick(tick) for strategy in self.strategies]
        operations = [op for op in operations if op]
        # TODO: Add risk management/operations consolidation here
        for operation in itertools.chain(*operations):
            operation(self.broker)

    def stop(self):
        click.secho('\nSIGINT received, shutting down cleanly...', fg='yellow')
        self._stop_requested = True
        self._main_loop.join()
