# -*- coding: utf-8 -*-

import json
from time import sleep

import requests
import lib.oandapy.oandapy as oandapy


class DataFeed(object):
    pass


class MyStreamer(oandapy.Streamer):
    def __init__(self, *args, **kwargs):
        oandapy.Streamer.__init__(self, *args, **kwargs)
        self.ticks = 0

    def on_success(self, data):
        self.ticks += 1
        print data
        if self.ticks == 10:
            self.disconnect()

    def on_error(self, data):
        self.disconnect()