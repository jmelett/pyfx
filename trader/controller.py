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


class ControllerBase(object):
    """
    A controller class takes care to run the actions returned by the strategies
    for each clock tick. How exactly this is implemented is deferred to the
    concrete subclass.
    """
    def __init__(self, clock, broker, strategies):
        self._clock = clock
        self._broker = broker
        self._strategies = strategies

    def initialize(self):
        for strategy in self._strategies:
            strategy.bind(self._broker)

    def run(self):
        raise NotImplementedError()

    def run_until_stopped(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def execute_tick(self, tick):
        raise NotImplementedError()


class ThreadedControllerMixin(object):
    def __init__(self, *args, **kwargs):
        super(ThreadedControllerMixin, self).__init__(*args, **kwargs)
        self._stop_requested = False
        self._main_loop = None

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
        self.initialize()
        for tick in self._clock:
            if self._stop_requested:
                return
            self.execute_tick(tick)
            if self._stop_requested:
                return

    def stop(self):
        click.secho('\nSIGINT received, shutting down cleanly...', fg='yellow')
        self._stop_requested = True
        self._main_loop.join()


class Controller(ThreadedControllerMixin, ControllerBase):
    def execute_tick(self, tick):
        operations = [strategy.tick(tick) for strategy in self._strategies]
        operations = [op for op in operations if op]
        # TODO: Add risk management/operations consolidation here
        for operation in itertools.chain(*operations):
            operation(self._broker)
