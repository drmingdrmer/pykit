#!/usr/bin/env python
# coding: utf-8

import heapq
import yaml
from collections import namedtuple

from . import cat
from pykit import timeutil
from pykit import strutil
from pykit.strutil import (red, blue, yellow, green)

DEBUG = True
DEBUG = False

time_fmt = '%d-%b-%Y %H:%M:%S'

RawEntry = namedtuple('RawEntry', [
        "raw",
        "index",

        "date",
        "time",
        "ts",
        "query",
        "level",

        "remote",
        "server",
        "view",
        "q_type",
        "ack_status",
        "serial",
        "flags",
        "domain",
        "network",
        "query_type",
        "answer",
        "eee",
        "edns_client"
])



class CompareError(Exception):
    pass


class TooFewInputFiles(CompareError):
    pass


class Entry(RawEntry):
    def __init__(self, *args, **kwargs):
        super(Entry, self).__init__(*args, **kwargs)

    def __cmp__(self, other):
        a, b = self[7:], other[7:]
        if a < b:
            rst = -1
        elif a == b:
            rst = 0
        else:
            rst = 1

        return rst

    def __lt__(self, other):

        a, b = self[7:], other[7:]
        if a < b:
            rst = -1
        elif a == b:
            rst = 0
        else:
            rst = 1

        return rst < 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __str__(self):
        return '{remote} {date} {time}'.format(**self._asdict())

class LineDiff(object):

    read_cnt = 50
    max_time_shift = 2.0 # second

    def __init__(self, paths, max_time_diff=1.0):

        if len(paths) < 2:
            raise TooFewInputFiles('need at least 2 input to compare'
                                   ' but only: ' + repr(paths))

        self.paths = paths
        self.bufs = [[] for x in paths]
        self.cats = []

        for p in paths:
            self.cats.append(cat.Cat(p, strip=True).iterate(timeout=3600))

        self.stat = {
                'matched': 0,
                'unmatched': [0 for x in self.paths], 
                'read': [0 for x in self.paths],
        }

    def _pop_iter(self, buf):
        while len(buf) > 0:
            yield heapq.heappop(buf)

    def diff(self):

        while True:

            self.feed_buf()

            n = len(self.bufs)
            max_ts = 0
            unmatched_entries = []

            # itr_sorted yield all element in order.
            itr_sorted = heapq.merge(*[self._pop_iter(x) for x in self.bufs])

            # itr_same yield a list of equal element from itr_sorted.
            itr_same = self.get_same_entries(itr_sorted, n)

            while True:

                try:
                    same_entries = itr_same.next()
                    max_ts = max([max_ts, same_entries[0].ts])

                    if len(same_entries) == n:
                        dd('matched: ', str(same_entries[0]))
                        self.stat['matched'] += n
                    else:
                        unmatched_entries.extend(same_entries)

                except StopIteration as e:
                    dd('buffer exhausted')
                    break

            self.put_to_buf(unmatched_entries, max_ts)

            _ok('stat:')
            _ok(yaml.dump(self.stat))

            # _warn('unmatched:')
            # for i, b in enumerate(self.bufs):
            #     _warn('    ==== only in ', self.paths[i])
            #     for ent in b:
            #         self.stat['unmatched'][ent.index] += 1
            #         _warn('    ', ent)

    def get_same_entries(self, itr, most):

        rst = []
        try:
            ent = itr.next()
            rst = [ent]

            self.stat['read'][ent.index] += 1
            dd('<< read in: ', ent.index, ' ', ent)

            for ent in itr:

                self.stat['read'][ent.index] += 1
                dd('<< read in: ', ent.index, ' ', ent)

                if rst[0] == ent and len(rst) < most:
                    rst.append(ent)
                else:
                    yield rst
                    rst = [ent]

        except StopIteration as e:
            pass

        if len(rst) > 0:
            yield rst

    def put_to_buf(self, unmatched_entries, max_ts):

        for ent in unmatched_entries:

            if ent.ts < max_ts - self.max_time_shift:
                _warn('unmatched: from {index}-th input:'.format(index=ent.index),
                      '{ent}'.format(ent=ent))
                self.stat['unmatched'][ent.index] += 1
            else:
                dd('postponed: ', ent)
                heapq.heappush(self.bufs[ent.index], ent)

    def feed_buf(self):

        for i, c in enumerate(self.cats):
            buf = self.bufs[i]

            for j in range(self.read_cnt):
                ent = parse_log(i, c.next())
                heapq.heappush(buf, ent)


def dd(*args):
    if DEBUG:
        _output(blue, *args)

def _ok(*args):
    _output(green, *args)

def _warn(*args):
    _output(yellow, *args)

def _output(clr, *args):
    print clr(''.join([str(x) for x in args]))


def parse_log(idx, line):

    # 日志格式
    # ===================================
    # 字段描述：
    # xxx   : 常量
    # <xxx> : 变量
    # [xxx] ：可没有
    # <date> <time> queries: log_level: |<remote_address#port>|<dns_server>|<view>|<q_type>|<ack_status>|<serial>|<flags>|<domain>|<network>|<query_type>|[<answer>]|[E]|[<edns_client>]|

    # 例子：
    # 20-Dec-2017 14:26:48.136 queries: info: |117.135.192.98#39672|120.192.85.55|yd_guizhou|QUERY|NOERROR|39644| qr aa cd|zbestv.v.bsgslb.cn|IN|A|117.139.19.149;117.175.90.46;|E|116.206.137.0/32/24|

    (subject,
     remote,
     server,
     view,
     q_type,
     ack_status,
     serial,
     flags,
     domain,
     network,
     query_type,
     answer,
     eee,
     edns_client,
     _,
    ) = line.split('|')

    d, t, q, lvl = subject.strip().split(' ')
    t, msec = t.split('.')
    msec = float('0.' + msec)
    ts = timeutil.utc_datetime_to_ts(timeutil.parse(d + ' ' + t, time_fmt)) + msec


    answer = tuple(sorted(answer.strip(';').split(';')))

    return Entry(
        line,
        idx,
        d,
        t,
        ts,
        q,
        lvl,

        remote,
        server,
        view,
        q_type,
        ack_status,
        serial,
        flags,
        domain,
        network,
        query_type,
        answer,
        eee,
        edns_client
    )

# ld = LineDiff(['bind.log', 'dpdk.log'])
# ld.diff()
