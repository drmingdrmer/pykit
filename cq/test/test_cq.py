import random
import unittest

import time

from collections import deque
from pykit import heap
from pykit import ututil
from pykit import threadutil
import threading

dd = ututil.dd


class X(object):

    def __init__(self, val):
        self.x = val

    def __lt__(self, b):
        return self.x < b.x

    def __str__(self):
        return str(self.x)


class TestDeque(unittest.TestCase):

    def test_bench_deque(self):
        n = 1024 * 100

        dq = deque()

        with ututil.Timer() as t:
            for ii in xrange(n):
                dq.append(ii)
                dq.popleft()

            spent = t.spent()

            print 'spent, us/call: {us}'.format(us=spent*1000*1000/n)

    def test_bench_deque_2p2c(self):

        n = 1024 * 10
        n_pro = 1
        n_con = 10
        lk = threading.RLock()

        sess = {'running': True, 'rst':[0] * n_con}

        dq = deque()

        def producer():
            for ii in xrange(n):
                with lk:
                    dq.append(ii)

        def consumer(i):
            while True:
                try:
                    with lk:
                        dq.popleft()
                        # time.sleep(0.1)
                        sess['rst'][i] += 1
                except IndexError:
                    if sess['running']:
                        time.sleep(0.01)
                        continue
                    else:
                        return

        with ututil.Timer() as t:

            pros = [threadutil.start_daemon(producer) for x in range(n_pro)]
            cons = [threadutil.start_daemon(consumer, args=(x, )) for x in range(n_con)]

            for pro in pros:
                pro.join()

            sess['running'] = False
            for con in cons:
                con.join()

            print sess
            print sum(sess['rst'])
            print sum(sess['rst']) == n * n_pro

            spent = t.spent()

            print 'spent, us/call: {us}'.format(us=spent*1000*1000/(n*n_pro))

