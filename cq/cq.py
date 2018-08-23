#!/usr/bin/env python
# coding: utf-8

from collections import deque
from collections import namedtuple
import threading

Cursor = namedtuple('Cursor', 'leftstart leftend rightstart rightend')

class Consumer(object):
    unset = {}
    def __init__(self):
        self.ev = threading.Event()
        self.val = self.unset
        self.lock = threading.RLock()

class CQueue(object):

    def __init__(self, size):
        self.dq = deque((), size)
        self.operation_dq = deque()
        self.cursor = Cursor(0, 0, 0, 0)
        self.lock = threading.RLock()

    def put(self, val):

        with self.lock:

            c = self.cursor

            if c.rightend - c.leftstart == size:
                raise IndexError()

    def get(self, consumer):

        try:
            v = self.dq.popleft()
            return v
        except IndexError:
            pass

        consumer.ev.clear()
        consumer.val = None

        self.operation_dq.append(consumer)

        try:
            v = self.dq.popleft()
        except IndexError:
            consumer.wait()
        else:
            cc = self.operation_dq[0]
            if cc is not consumer:
                consumer.wait()

            # the first is me
            



        with self.lock:
            c = self.cursor
            if c.leftend >= c.rightstart:
                raise IndexError()

