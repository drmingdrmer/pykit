#!/usr/bin/env python2
# coding: utf-8

import unittest

from pykit import cluster
from pykit import rangeset


class TestClusterBlockDesc(unittest.TestCase):

    def test_blockdesc(self):

        block_id = 'd1g0006300000001230101c62d8736c72800020000000001'
        cases = ((None,
                  {'block_id': None,
                   'size': 0,
                   'range': None,
                   'is_del': 1}),

                 ({'block_id': block_id,
                   'range': ['a', 'b'],
                   'size': 34,
                   'is_del': 0},
                  {'block_id': cluster.BlockID.parse(block_id),
                   'range': rangeset.Range('a', 'b'),
                   'size': 34,
                   'is_del': 0}),

                 ({'block_id': cluster.BlockID.parse(block_id),
                   'range': rangeset.Range('b', 'bb')},
                  {'block_id': cluster.BlockID.parse(block_id),
                   'range': rangeset.Range('b', 'bb'),
                   'size': 0,
                   'is_del': 1, })
                 )

        for b, expected in cases:
            if b is None:
                blk = cluster.BlockDesc()
            else:
                blk = cluster.BlockDesc(b)

            self.assertEqual(expected, blk)

        self.assertRaises(ValueError, cluster.BlockDesc, is_del='a')
        self.assertRaises(ValueError, cluster.BlockDesc, size='a')
        self.assertRaises(KeyError, cluster.BlockDesc, a=3)